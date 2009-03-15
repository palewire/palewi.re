import cPickle as pickle
from coltrane.models import *
from tagging.models import Tag
from django.contrib.comments.models import Comment
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.template.defaultfilters import slugify

def posts():
	"""
	Load legacy blog posts from Wordpress into the new Django system.
	
	Example usage::
	
		>> from legacy import load
		>> load.posts()
		
	"""
	
	infile = open("../legacydb/dumps/posts.dump", 'r')
	posts = pickle.load(infile)
	infile.close()
	ben = User.objects.get(username='ben')
	for record in posts:
		_id, post_date, post_slug, post_title, post_content = record
		p, created = Post.objects.get_or_create(
			wordpress_id = _id,
			title = post_title,
			slug = post_slug,
			body_markup = post_content,
			pub_date = post_date,
			status = 1,
			author = ben
		)
		if created:
			print "Added %s" % p.title
		
		
def comments():
	infile = open("../legacydb/dumps/comments.dump", 'r')
	comments = pickle.load(infile)
	infile.close()
	ctype = ContentType.objects.get(name='post')
	site = Site.objects.all()[0]
	for record in comments:
		comment_post_id, comment_author, comment_author_email, comment_author_url, comment_author_ip, comment_date, comment_content = record
		post = Post.objects.get(wordpress_id=comment_post_id)
		c, created = Comment.objects.get_or_create(
			user_name = comment_author[:50],
			user_email = comment_author_email,
			user_url = comment_author_url,
			ip_address = comment_author_ip,
			submit_date = comment_date,
			comment = comment_content,
			is_public = True,
			content_type = ctype,
			object_pk = str(post.pk),
			site = site,
		)
		if created:
			print "Added comment by %s on %s" % (c.user_name, post.title)

def is_public():
	for c in Comment.objects.all():
		c.is_public = True
		c.save()
	
def cats():
	"""
	Load legacy categories from Wordpress into the new Django system, linking them to their posts.
	
	Example usage::
	
		>> from legacy import load
		>> load.cats()
		
	"""
	infile = open("../legacydb/dumps/categories.dump", 'r')
	cats = pickle.load(infile)
	infile.close()
	for record in cats:
		post_id, name = record
		c, created = Category.objects.get_or_create(title=name.strip(), slug=slugify(name.strip()))
		if created:
			print "Added category %s" % c.title
		try:
			p = Post.objects.get(wordpress_id=post_id)
			p.categories.add(c)
			p.save()
			print "Added %s to %s" % (c.title, p.title)
		except Post.DoesNotExist:
			pass
		except:
			raise

def tags():
	from tagging.utils import edit_string_for_tags
	infile = open("../legacydb/dumps/tags.dump", 'r')
	tags = pickle.load(infile)
	infile.close()
	for record in tags:
		post_id, name = record
		try:
			p = Post.objects.get(wordpress_id=post_id)
			#print "%s => %s" % (p.title, name)
			tag = u'"%s"' % name[:50].replace('"', '').strip()
			Tag.objects.add_tag(p, tag)
			print "Added %s to %s" % (name, p.title)
		except Post.DoesNotExist:
			pass
	
	for post in Post.objects.all():
		tags = Tag.objects.get_for_object(post)
		post.tags = edit_string_for_tags(tags)[:250]
		post.save()

def run():
	posts()
	cats()
	tags()
	comments()
