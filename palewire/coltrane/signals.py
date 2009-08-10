# Signals
from django.db.models import signals
from django.dispatch import dispatcher
from django.contrib.comments.signals import comment_was_posted

# Models
from django.contrib.contenttypes.models import ContentType


def create_ticker_item(sender, instance, signal, *args, **kwargs):
	"""
	When a new object is saved, it will be added to Ticker model and therefore the site's front page.
	"""
	from coltrane.models import Ticker
	# Check to see if the object was just created for the first time
	if 'created' in kwargs and instance.__class__.__name__ != 'Comment':
		if kwargs['created']:
			ctype = ContentType.objects.get_for_model(instance)
			pub_date = instance.pub_date
			Ticker.objects.get_or_create(content_type=ctype, object_id=instance.id, pub_date=pub_date)
	# Check to see if the object is a comment, and it has been approved
	if instance.__class__.__name__ == 'Comment':
		if instance.is_public:
			ctype = ContentType.objects.get_for_model(instance)
			pub_date = instance.submit_date
			Ticker.objects.get_or_create(content_type=ctype, object_id=instance.id, pub_date=pub_date)


def delete_ticker_item(sender, instance, signal, *args, **kwargs):
	"""
	When an object is deleted, its ticker item will also be wiped out.
	"""
	from coltrane.models import Ticker
	ctype = ContentType.objects.get_for_model(instance)
	if instance.__class__.__name__ == 'Comment':
		print "COMMENT!"
		pub_date = instance.submit_date
	else:
		pub_date = instance.pub_date
	try:
		t = Ticker.objects.get(content_type=ctype, object_id=instance.id, pub_date=pub_date)
		t.delete()
	except Ticker.DoesNotExist:
		pass
		

def category_count(sender, instance, signal, *args, **kwargs):
	"""
	Count the number of live posts associated with each Category record -- and save it back to the model.
	"""
	from coltrane.models import Category
	for cat in Category.objects.all():
		cat.post_count = cat.get_live_post_count()
		cat.save()
		

def on_comment_was_posted(sender, comment, request, *args, **kwargs):
	"""
	Spam guard for comments.
	
	Lifted from this guy: http://sciyoshi.com/blog/2008/aug/27/using-akismet-djangos-new-comments-framework/
	"""

	from django.contrib.sites.models import Site
	from django.conf import settings
	from django.template import Context, loader
	from django.core.mail import send_mail

	try:
		from akismet import Akismet
	except:
		return

	# use TypePad's AntiSpam if the key is specified in settings.py
	if hasattr(settings, 'TYPEPAD_ANTISPAM_API_KEY'):
		ak = Akismet(
			key=settings.TYPEPAD_ANTISPAM_API_KEY,
			blog_url='http://%s/' % Site.objects.get(pk=settings.SITE_ID).domain
		)
		ak.baseurl = 'api.antispam.typepad.com/1.1/'
	else:
		ak = Akismet(
			key=settings.AKISMET_API_KEY,
			blog_url='http://%s/' % Site.objects.get(pk=settings.SITE_ID).domain
		)

	if ak.verify_key():
		data = {
			'user_ip': request.META.get('REMOTE_ADDR', '127.0.0.1'),
			'user_agent': request.META.get('HTTP_USER_AGENT', ''),
			'referrer': request.META.get('HTTP_REFERER', ''),
			'comment_type': 'comment',
			'comment_author': comment.user_name.encode('utf-8'),
		}

		# If it's spam...
		if ak.comment_check(comment.comment.encode('utf-8'), data=data, build_data=True):
			comment.flags.create(
				user=comment.content_object.author,
				flag='spam'
			)
			comment.is_public = False
			comment.is_removed = True
			comment.save()
		
		# If it's not...
		else:
			# Send an email
			recipient_list = [manager_tuple[1] for manager_tuple in settings.MANAGERS]
			t = loader.get_template('comments/comment_notification_email.txt')
			c = Context({ 'comment': comment, 'content_object': comment.content_object })
			subject = '[%s] New comment posted on "%s"' % (Site.objects.get_current().name,
			                                                  comment.content_object)
			message = t.render(c)
			send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, fail_silently=True)

comment_was_posted.connect(on_comment_was_posted)