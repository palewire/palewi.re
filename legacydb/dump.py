# Should switch this to pickles

from legacydb.legacy.models import *
import codecs
from django.utils.encoding import smart_str
import os
import csv
import cPickle as pickle

def posts():
	path = "dumps/posts.dump"
	out = codecs.open(path, 'w', 'utf-8')
	data = []
	for post in WpPosts.objects.filter(post_status='publish', post_type='post'):
		record = [post.id, post.post_date, post.post_name, post.post_title.strip(), post.post_content.strip()]
		data.append([smart_str(i) for i in record])
	pickle.dump(data, out)
	out.close()

def comments():
	path = "dumps/comments.dump"
	out = codecs.open(path, 'w', 'utf-8')
	data = []
	for i in WpComments.objects.filter(comment_approved='1'):
		record = [i.comment_post_id, i.comment_author, i.comment_author_email, i.comment_author_url, i.comment_author_ip, i.comment_date, i.comment_content]
		data.append([smart_str(i) for i in record])
	#print data
	pickle.dump(data, out)
	out.close()

def cats():
	path = "dumps/categories.dump"
	out = codecs.open(path, 'w', 'utf-8')
	data = []
	for i in WpTermTaxonomy.objects.filter(taxonomy='category'):
		post_ids = WpTermRelationships.objects.filter(term_taxonomy_id=i.term_taxonomy_id)
		name = WpTerms.objects.get(term_id=i.term_id).name
		for post in post_ids:
			data.append([post.object_id, name])
	pickle.dump(data, out)
	out.close()
	
def tags():
	path = "dumps/tags.dump"
	out = codecs.open(path, 'w', 'utf-8')
	data = []
	for i in WpTermTaxonomy.objects.filter(taxonomy='post_tag'):
		post_ids = WpTermRelationships.objects.filter(term_taxonomy_id=i.term_taxonomy_id)
		name = WpTerms.objects.get(term_id=i.term_id).name
		for post in post_ids:
			data.append([post.object_id, name])
	pickle.dump(data, out)
	out.close()
	
def run():
	posts()
	comments()
	cats()
	tags()

