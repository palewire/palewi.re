from legacydb.legacy.models import *
import codecs
from django.utils.encoding import smart_str
import os
import csv

def get_csv_table(path):
	app_dir = os.path.dirname(__file__)
	data_file = os.path.join(app_dir, path)
	return csv.reader(open(data_file), delimiter="|", quotechar='^')

def posts():
	path = "dumps/posts.dump"
	out = codecs.open(path, 'w', 'utf-8')
	for post in WpPosts.objects.filter(post_status='publish', post_type='post'):
		record = [post.id, post.post_date, post.post_title.strip(), post.post_content.strip()]
		print >> out, "|".join([u'^%s^' % i for i in record])
	out.close()

def comments():
	path = "dumps/comments.dump"
	out = codecs.open(path, 'w', 'utf-8')
	for i in WpComments.objects.filter(comment_approved='1'):
		record = [i.comment_post_id, i.comment_author, i.comment_author_email, i.comment_author_url, i.comment_author_ip, i.comment_date, i.comment_content]
		print >> out, "|".join([u'^%s^' % i for i in record])
	out.close()

def cats():
	path = "dumps/categories.dump"
	out = codecs.open(path, 'w', 'utf-8')
	for i in WpTermTaxonomy.objects.filter(taxonomy='category'):
		post_ids = WpTermRelationships.objects.filter(term_taxonomy_id=i.term_taxonomy_id)
		name = WpTerms.objects.get(term_id=i.term_id).name
		for post in post_ids:
			print >> out, "|".join(map(str, [post.object_id, name]))
	out.close()
	
def tags():
	path = "dumps/tags.dump"
	out = codecs.open(path, 'w', 'utf-8')
	for i in WpTermTaxonomy.objects.filter(taxonomy='post_tag'):
		post_ids = WpTermRelationships.objects.filter(term_taxonomy_id=i.term_taxonomy_id)
		name = WpTerms.objects.get(term_id=i.term_id).name
		for post in post_ids:
			print >> out, "|".join(map(str, [post.object_id, name]))
	out.close()
	
	#result = get_csv_table(path)
	#for i, row in enumerate(result):
	#	print row
	
	

