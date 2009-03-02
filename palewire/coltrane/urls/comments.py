from django.conf.urls.defaults import *

from django.contrib.comments.models import Comment
from django.contrib.contenttypes.models import ContentType

# For the comment-based generic views
comments = {
	'queryset': Comment.objects.filter(is_public= \
				True, content_type__app_label='coltrane').order_by('-submit_date'),
}

# The comment views
urlpatterns = patterns('django.views.generic.list_detail',

	(r'^(?P<page>[0-9]+)/$',
	'object_list', dict(comments, 
						paginate_by=25, 
						template_name= 'coltrane/comment_list.html')),

)