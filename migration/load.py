#!/usr/bin/env python
import os
import MySQLdb

from django.contrib.auth.models import User
from django.contrib.comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from coltrane.models import Post, Category

data_dir = os.path.dirname(__file__)

def mysql_conn():
	DB = 'myblog'
	DB_HOST = 'localhost'
	DB_USER = 'root'
	DB_PASSWORD = ''
	conn = MySQLdb.Connection(db=DB, host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD)
	return conn.cursor()

def posts():
	cursor = mysql_conn()

	select_posts = "SELECT ID, post_date, post_title, post_name, post_content FROM wp_posts WHERE post_status = 'publish' AND post_type = 'post';"

	cursor.execute(select_posts)

	for row in cursor.fetchall():
		(wp_id, date, hed, slug, body) = row
		try:
			p = Post.objects.get(wordpress_id = wp_id)
			print "Skipping post %s" % hed
		
		except Post.DoesNotExist:
			print "Adding post %s" % hed
			ben = User.objects.get(id=1)
			p = Post(
				wordpress_id = wp_id, 
				pub_date = date,
				title = hed,
				slug = slug,
				author = ben,
				body = body,
				enable_comments = True,
				status = 1,
			)
			p.save()
			
	cursor.close()

def comments():
	cursor = mysql_conn()
	
	select_comments = "SELECT comment_post_ID, comment_author, comment_author_email, comment_author_url, comment_author_IP, comment_date, comment_content FROM wp_comments WHERE comment_approved = '1';"
	
	cursor.execute(select_comments)
	
	for row in cursor.fetchall():
		(post_id, author, email, url, ip, date, content) = row
		
		try:
			p = Post.objects.get(wordpress_id = post_id)
			print "Adding a comment from %s to %s" % (author, p.title)
		
			ct = ContentType.objects.get(model='post')
			s = Site.objects.get(id=2)
		
			c = Comment(
				user_name = author[:50],
				user_email = email,
				user_url = url,
				comment = content,
				ip_address = ip,
				is_public = True,
				submit_date = date,
				content_type = ct,
				object_pk = p.id,
				site = s,
				)
			
			c.save()
		
		except Post.DoesNotExist:
			print "Could not find post no. %s" % post_id
		
		
	