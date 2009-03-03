import cPickle as pickle
from coltrane.models import *
from django.contrib.auth.models import User

def posts():
	infile = open("../legacydb/dumps/posts.dump", 'r')
	posts = pickle.load(infile)
	infile.close()
	ben = User.objects.get(first_name='Ben')
	for record in posts:
		id, post_date, post_slug, post_title, post_content = record
		Post.objects.get_or_create(
			wordpress_id = id,
			title = post_title,
			slug = post_slug,
			body = post_content,
			pub_date = post_date,
			status = 1,
			author = ben
		)
		
		
def comments():
	pass
	
def cats():
	pass
	
def tags():
	pass
