import datetime, time
from django.db.models import get_model
from tagging.models import Tag, TaggedItem
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.views.generic.list_detail import object_list
from coltrane.models import Post, Category, Link, Photo


def index(request):
	"""
	The homepage of the site, which simply redirects to the latest post.
	"""
	latest_post = Post.live.latest()
	args = map(str, [latest_post.pub_date.year, latest_post.pub_date.month, latest_post.pub_date.day, latest_post.slug])
	return post_detail(request, *args)


def post_detail(request, year, month, day, slug):
	"""
	A detail page that shows an entire post.
	"""
	date_stamp = time.strptime(year+month+day, "%Y%m%d")
	pub_date = datetime.date(*date_stamp[:3])
	post = get_object_or_404(Post,	pub_date__year=pub_date.year,
									pub_date__month=pub_date.month,
									pub_date__day=pub_date.day,
									slug=slug)
	related_posts = TaggedItem.objects.get_related(post, get_model('coltrane', 'post'))[:5]
	return render_to_response('coltrane/post_detail.html',
								{ 'object': post,
								  'related_posts': related_posts })
								

def category_detail(request, slug):
	"""
	A list that reports all the posts in a particular category.
	"""
	category = get_object_or_404(Category, slug=slug)
	return object_list(request, queryset = category.post_set.all(), 
						extra_context = {'category': category },
						template_name = 'coltrane/category_detail.html')


def tag_detail(request, tag):
	"""
	A list that reports all of the content with a particular tag.
	"""
	# Pull the tag
	tag = tag.replace("-", " ")
	tag = get_object_or_404(Tag, name=tag)
	
	# Pull all the items with that tag.
	taggeditem_list = tag.items.all()
	
	# Loop through the tagged items and return just the items
	object_list = [i.object for i in taggeditem_list]
	
	# Now resort them by the pub_date attribute we know each one should have
	object_list.sort(key=lambda x: x.pub_date, reverse=True)

	# Pass it out
	return render_to_response('coltrane/tag_detail.html', { 
			'tag': tag, 
			'object_list': object_list,
		})
		
