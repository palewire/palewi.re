# Templating
from django import template
register = template.Library()

# Models
from correx.models import Change
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db.models import get_app, get_model
from django.contrib.contenttypes.models import ContentType

# Text manipulation
from django.utils.translation import ugettext_lazy as _


class ChangesByObjectNode(template.Node):
	def __init__(self, obj, num, varname):
		self.obj = template.Variable(obj)
		self.num = int(num)
		self.varname = varname

	def render(self, context):
		resolved_obj = self.obj.resolve(context)
		try:
			ct = ContentType.objects.get_for_model(resolved_obj)
		except:
			raise template.TemplateSyntaxError (_("model could not be found for object"))
		context[self.varname] = \
			Change.objects.filter(is_public=True, content_type=ct, object_id=resolved_obj.pk).order_by('-pub_date')[:self.num]
		return ''


def do_changes_for_object(parser, token):
	""" 
	Gets a list of the changes for a particular object.
	
	Syntax::

		{% get_changes_for_object [object] [count] as [varname] %}
	
	Example usage::

		{% load correx_tags %}
		{% get_changes_for_object object 5 as change_list %}
		{% for change in change_list %}
			<li>{{ change.pub_date }} - {{ change.get_change_type_display }} - {{ change.description }}</li>
		{% endfor %}
		
	Good for pulling the list into object_detail pages.
		
	"""
	bits = token.contents.split()
	if len(bits) != 5:
		raise template.TemplateSyntaxError (_("get_changes_for_object tag takes exactly five arguments"))
	if bits[3] != 'as':
		raise template.TemplateSyntaxError(_("fourth argument to %s tag must be 'as'") % bits[0])
	return ChangesByObjectNode(bits[1], bits[2], bits[4])


class ChangesByModelNode(template.Node):
	def __init__(self, model, num, varname):
		self.model = model
		self.num = int(num)
		self.varname = varname

	def render(self, context):
		model = get_model(*self.model.split('.'))
		if model is None:
			raise template.TemplateSyntaxError(_('get_changes_for_model tag was given an invalid model: %s') % self.model)
		ct = ContentType.objects.get_for_model(model)
		context[self.varname] = \
			Change.objects.filter(is_public=True, content_type=ct).order_by('-pub_date')[:self.num]
		return ''


def do_changes_for_model(parser, token):
	""" 
	Gets a list of the most recent changes for particular model.

	Syntax::
	
		{% get_changes_for_model [app_label].[model_name] [count] as [varname] %}

	Example usage::
	
		{% load correx_tags %}
		{% get_changes_for_model newspaper.Article 5 as change_list %}
		{% for change in change_list %}
			<li>{{ change.pub_date}} - {{ change.get_change_type_display }} - {{ change.description }}</li>
		{% endfor %}

	"""
	bits = token.contents.split()
	if len(bits) != 5:
		raise template.TemplateSyntaxError (_("get_changes_for_model tag takes exactly five arguments"))
	if bits[3] != 'as':
		raise template.TemplateSyntaxError(_("fourth argument to %s tag must be 'as'") % bits[0])
	return ChangesByModelNode(bits[1], bits[2], bits[4])


class ChangesByAppNode(template.Node):
	def __init__(self, app_label, num, varname):
		self.app_label = app_label
		self.num = int(num)
		self.varname = varname

	def render(self, context):
		try:
			ct_set = ContentType.objects.filter(app_label__icontains=self.app_label)
		except:
			raise template.TemplateSyntaxError (_("app_label %s could not be found") % self.app_label)
		context[self.varname] = \
			Change.objects.filter(is_public=True, content_app=self.app_label).order_by('-pub_date')[:self.num]
		return ''


def do_changes_for_app(parser, token):
	""" 
	Gets a list of the most recent changes for particular app.

	Syntax::

		{% get_changes_for_app [app_label] [count] as [varname] %}

	Example usage::

		{% load correx_tags %}
		{% get_changes_for_app newspaper 5 as change_list %}
		{% for change in change_list %}
			<li>{{ change.pub_date}} - {{ change.get_change_type_display }} - {{ change.description }}</li>
		{% endfor %}

	Good for sidebars or pulling in a list on a standalone or showcase app.

	"""
	bits = token.contents.split()
	if len(bits) != 5:
		raise template.TemplateSyntaxError (_("get_changes_for_app tag takes exactly five arguments"))
	if bits[3] != 'as':
		raise template.TemplateSyntaxError(_("fourth argument to %s tag must be 'as'") % bits[0])
	return ChangesByAppNode(bits[1], bits[2], bits[4])


class ChangesBySiteNode(template.Node):
	def __init__(self, id, num, varname):
		self.id = id
		self.num = int(num)
		self.varname = varname

	def render(self, context):
		try:
			site = Site.objects.get(pk=self.id)
		except User.DoesNotExist:
			raise template.TemplateSyntaxError (_("Site id %s could not be found") % self.username)
		context[self.varname] = \
			Change.objects.filter(is_public=True, site=site).order_by('-pub_date')[:self.num]
		return ''


def do_changes_for_site(parser, token):
	""" 
	Gets a list of the most recent changes for particular site.

	Syntax::

		{% get_changes_for_site [site_id] [count] as [varname] %}

	Example usage::

		{% load correx_tags %}
		{% get_changes_for_site 1 5 as change_list %}
		{% for change in change_list %}
			<li>{{ change.pub_date}} - {{ change.get_change_type_display }} - {{ change.description }}</li>
		{% endfor %}

	"""
	bits = token.contents.split()
	if len(bits) != 5:
		raise template.TemplateSyntaxError (_("get_changes_for_site tag takes exactly five arguments"))
	if bits[3] != 'as':
		raise template.TemplateSyntaxError(_("fourth argument to %s tag must be 'as'") % bits[0])
	return ChangesBySiteNode(bits[1], bits[2], bits[4])


class ChangesByUserNode(template.Node):
	def __init__(self, username, num, varname):
		self.username = username
		self.num = int(num)
		self.varname = varname

	def render(self, context):
		try:
			user = User.objects.get(username__iexact=self.username)
		except User.DoesNotExist:
			raise template.TemplateSyntaxError (_("User named %s could not be found") % self.username)
		context[self.varname] = \
			Change.objects.filter(is_public=True, user=user).order_by('-pub_date')[:self.num]
		return ''


def do_changes_for_user(parser, token):
	""" 
	Gets a list of  the most recent changes for particular user.
	
	Syntax::
	
		{% get_changes_for_user [username] [count] as [varname] %}

	Example usage::

		{% load correx_tags %}
		{% get_changes_for_user Otis 5 as change_list %}
		{% for change in change_list %}
			<li>{{ change.pub_date}} - {{ change.get_change_type_display }} - {{ change.description }}</li>
		{% endfor %}

	Good for sidebars or pulling in a list on a standalone or showcase app.

	"""
	bits = token.contents.split()
	if len(bits) != 5:
		raise template.TemplateSyntaxError (_("get_changes_for_user tag takes exactly five arguments"))
	if bits[3] != 'as':
		raise template.TemplateSyntaxError(_("fourth argument to %s tag must be 'as'") % bits[0])
	return ChangesByUserNode(bits[1], bits[2], bits[4])


class LatestChangesNode(template.Node):
	def __init__(self, num, varname):
		self.num = int(num)
		self.varname = varname

	def render(self, context):
		context[self.varname] = Change.objects.live().order_by('-pub_date')[:self.num]
		return ''


def do_latest_changes(parser, token):
	""" 
	Gets a list of the most recent changes regardless of user, site, app, model or object.
	
	Syntax::

		{% get_latest_changes [count] as [varname] %}
	
	Example usage::

		{% load correx_tags %}
		{% get_latest_changes 5 as latest_changes %}
		{% for change in latest_changes %}
			<li>{{ change.pub_date}} - {{ change.get_change_type_display }} - {{ change.description }}</li>
		{% endfor %}
		
	Good for pulling the list into sidebars that run across an app or site.

	"""
	
	bits = token.contents.split()
	if len(bits) != 4:
		raise template.TemplateSyntaxError (_("get_latest_changes tag takes exactly four arguments"))
	if bits[2] != 'as':
		raise template.TemplateSyntaxError(_("third argument to %s tag must be 'as'") % bits[0])
	return LatestChangesNode(bits[1], bits[3])


# Register the tags
register.tag('get_changes_for_object', do_changes_for_object)
register.tag('get_changes_for_model', do_changes_for_model)
register.tag('get_changes_for_app', do_changes_for_app)
register.tag('get_changes_for_site', do_changes_for_site)
register.tag('get_changes_for_user', do_changes_for_user)
register.tag('get_latest_changes', do_latest_changes)