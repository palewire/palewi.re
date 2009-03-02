#!/usr/bin/python
# -*- encoding: utf-8 -*-

"""
dbpickle.py is a Django tool for saving all database objects into a
file or loading and storing them back into the database.  It's useful
for migrating from one database engine to another.

This version handles ForeignKeys which refer to the related model's
primary key.  ManyToMany relations are now supported, but OneToOne
relations are not.

You can also use you own plugin for pre-processing objects before
saving them into the database.	This is useful e.g. when a model has
changed and you're importing objects from an old version of the
database.  The plugin should be a Python program with a
``pre_save_hook(obj)`` and/or ``pre_walk_hook(obj)`` function which
returns True if it modified the object, otherwise False.


Usage example
=============

Let's suppose your project is using PostgreSQL and the database has
been populated using the app.

$ PYTHONPATH=/home/myproject DJANGO_SETTINGS_MODULE=settings \
  ./dbpickle.py --dump --file=myproject.pickle

At this point you could change the settings so that SQLite is used
instead of PostgreSQL.

$ PYTHONPATH=/home/myproject DJANGO_SETTINGS_MODULE=settings \
  /home/myproject/manage.py syncdb

(answer 'no' when asked about creating a superuser)

$ PYTHONPATH=/home/myproject DJANGO_SETTINGS_MODULE=settings \
  ./dbpickle.py --load --file=myproject.pickle

This would effectively convert your database from PostgreSQL to SQLite
through Django.
"""
#import os
#import sys
#os.environ['PYTHONPATH'] = '/Users/ben/Documents/Code/development/python/projects'
#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
#sys.path.append('/Users/ben/Documents/Code/development/python/projects')

from django.db import transaction
import cPickle
import logging
from django.db import models
from imp import load_source

try:
	set # Only available in Python 2.4+
except NameError:
	from sets import Set as set # Python 2.3 fallback

def dump(filepath):
	"""
	Pickle all Django objects from the database and save them into the
	given file.
	"""
	objects = {}   # model instances
	m2m_lists = [] # ManyToMany relations between model instances
	for model in models.get_models():
		meta = model._meta
		app, model_name = meta.app_label, meta.module_name

		print "Processing %s (%s)" % (app, model_name)
		
		# get all many-to-many relation field names for this model
		m2ms = [m2m.name for m2m in meta.many_to_many]

		for obj in model.objects.all():
			print 'dumping %s.%s %s' % (app, model_name, obj)
			logging.info('dumping %s.%s %s' % (app, model_name, obj))
			pk = obj._get_pk_val()
			objects[app, model_name, pk] = obj

			for m2m in m2ms:
				# store many-to-many related objects for every
				# many-to-many relation of this object
				foreign_objs = getattr(obj, m2m).all()
				print 'dumping %s.%s.%s x %d' % (app, model_name, m2m, len(foreign_objs))
				logging.info('dumping %s.%s.%s x %d' % (app, model_name, m2m, len(foreign_objs)))
				m2m_lists.append((obj, m2m, tuple(foreign_objs)))

	# pickle all objects and many-to-many relations on disk
	cPickle.dump((objects, m2m_lists), file(filepath, 'w'))


#@transaction.commit_on_success
def load(filepath, pluginpath=None):
	"""
	Unpickle Django objects from the given file and save them into the
	database.
	"""

	# load the plugin if specified on the command line
	if pluginpath:
		plugin = load_source('plugin', pluginpath)
	else:
		plugin = None

	# get the hook functions from the plugin
	hooks = {}
	for hookname in 'pre_save', 'pre_walk':
		hooks[hookname] = getattr(plugin, '%s_hook' % hookname, lambda obj: False)

	# unpickle objects and many-to-many relations from disk
	objects, m2m_lists = cPickle.load(file(filepath))

	# Find distinct models of all unpickled objects and delete all
	# objects before loading.  Note that models which have not been
	# dumped are not emptied.
	models = set( [obj.__class__ for obj in objects.itervalues()] )
	for model in models:
		for obj in model._default_manager.all():
			obj.delete()

	# load all objects
	while objects:
		key, obj = objects.popitem()
		load_recursive(objects, obj, hooks)

	# load all many-to-many relations
	for obj1, m2m, foreign_objs in m2m_lists:
		meta1 = obj1._meta
		for obj2 in foreign_objs:
			meta2 = obj2._meta
			logging.info('loading ManyToMany %s.%s.%s -> %s.%s.%s' % (
				meta1.app_label, meta1.module_name, obj1._get_pk_val(),
				meta2.app_label, meta2.module_name, obj2._get_pk_val()))
			getattr(obj1, m2m).add(obj2)

load = transaction.commit_on_success(load)


def load_recursive(objects, obj, hooks):
	"""
	Save the given object into the database.  If the object has
	ForeignKey relations to other objects, first make sure they are
	already saved (and repeat recursively).
	"""

	meta = obj._meta

	hooks['pre_walk'](obj)
	for field in meta.fields:
		if isinstance(field, models.ForeignKey):
			related_meta = field.rel.to._meta
			related_app = related_meta.app_label
			related_model = related_meta.module_name
			related_pk_val = getattr(obj, field.name+'_id')
			try:
				related_obj = objects.pop((related_app,
										   related_model,
										   related_pk_val))
				load_recursive(objects, related_obj, hooks)
			except KeyError:
				logging.debug('probably loaded already: '
							  '%(related_app)s.%(related_model)s '
							  '%(related_pk_val)s' % locals())

	logging.info('loading %s.%s %s' % (
		meta.app_label,
		meta.module_name,
		obj._get_pk_val()))
	try:
		hooks['pre_save'](obj)
		obj.save()
	except Exception, e:
		logging.error('%s while saving %s' % (e, obj))


if __name__ == '__main__':
	from optparse import OptionParser
	p = OptionParser()
	p.add_option('-d', '--dump', action='store_const', const='dump', dest='action', help='Dump all Django objects into a file')
	p.add_option('-l', '--load', action='store_const', const='load', dest='action', help='Load all Django objects from a file')
	p.add_option('-f', '--file', default='djangodb.pickle', help='Specify file path [djangodb.pickle]')
	p.add_option('-p', '--plugin', help='Use .py plugin for preprocessing objects to load')
	p.add_option('-v', '--verbose' , action='store_const', const=logging.DEBUG, dest='loglevel', help='Show verbose output for debugging')
	p.add_option('-q', '--quiet' , action='store_const', const=logging.FATAL, dest='loglevel', help='No output at all')
	(opts, args) = p.parse_args()
	loglevel = opts.loglevel or logging.INFO
	try:
		# Python 2.4+ syntax
		logging.basicConfig(level=loglevel, format='%(levelname)-8s %(message)s')
	except TypeError:
		# Python 2.3
		logging.basicConfig()
	if opts.action == 'dump':
		dump(opts.file)
	elif opts.action == 'load':
		load(opts.file, opts.plugin)
	else:
		print 'Please specify --dump or --load'
