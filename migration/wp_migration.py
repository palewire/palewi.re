from django.core.management import setup_environ
import settings
 
setup_environ(settings)
 
import MySQLdb
 
from coltrane.models import *
from datetime import datetime
from django.contrib.comments.models import Comment
 
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_unicode, force_unicode
 
 
host = "localhost"
user = "root"
password = ""
db = "myblog"
 
try:
	conn = MySQLdb.Connect(host=host, user=user, passwd=password, db=db)
except Exception, e:
	print e
	raise Exception('meeeh')
 
from django.contrib.auth.models import User
 
author = User.objects.get(username='ben')
posttype = ContentType.objects.get_for_model(Post)
 
prefix = 'wp_'
entries = {}
querydict = {'prefix' : prefix}

def LoadPosts():
	sql = """SELECT id, LEFT(post_name,50) as post_name, post_title, post_date, post_content
	FROM wp_posts WHERE post_type='post' and post_status = 'publish'"""
	c = conn.cursor()
	c.execute(sql)
	posts = {}
 
	for post_id, name, title, date, content in c.fetchall():
		print title
		e = Post(
		author = author,
		pub_date = date,
		slug = force_unicode(name),
		title = force_unicode(title),
		body = force_unicode(content),
		body_html = force_unicode(content),
		enable_comments = 1,
		status = 1
		)
		e.save()
		posts["p_%s" % post_id] = e

LoadPosts()

def LoadComments():
	sql = """select comment_content, comment_post_id, comment_author, comment_author_email,
	comment_author_url, comment_date_gmt, comment_author_ip
	from wp_comments where comment_approved = '1'
	"""
	c.execute(sql)
	results = c.fetchall()
	print "Comment count:", len(results)
	print "Post count:", len(posts)
 
	for content, post_id, comment_author, comment_author_email, comment_author_url, comment_date, author_ip in results:
		e = posts['p_%s' % post_id]
		comment = FreeThreadedComment(
		content_type= posttype,
		object_id = e.id,
		comment = content,
		name = comment_author[:127],
		website = comment_author_url,
		email = comment_author_email,
		date_submitted = comment_date,
		is_public = True,
		ip_address = author_ip,
		is_approved = True,
		)
		comment.save()
		comment.date_submitted = comment_date
		comment.date_modified = comment_date
		comment.save()