import datetime, time
from django.db.models import get_model
from tagging.models import Tag, TaggedItem
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list_detail import object_list
from coltrane.models import Post, Category, Link, Photo


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
	tag = tag.replace("-", " ")
	tag = get_object_or_404(Tag, name=tag)
	posts = Post.live.all()
	post_list = TaggedItem.objects.get_by_model(posts, tag)
	link_list = TaggedItem.objects.get_by_model(Link, tag)
	photo_list = TaggedItem.objects.get_by_model(Photo, tag)
	return render_to_response('coltrane/tag_detail.html', { 
			'tag': tag, 
			'post_list': post_list,
			'video_list': video_list,
			'link_list': link_list,
			'photo_list': photo_list,
		})
		
