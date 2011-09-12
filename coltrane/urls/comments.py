from django.conf.urls.defaults import *

from django.contrib.comments.models import Comment
from django.contrib.contenttypes.models import ContentType

# For the comment-based generic views
comments = {
    'queryset': Comment.objects.filter(is_public= \
                True, content_type__app_label='coltrane').order_by('-submit_date'),
}

# The comment views
urlpatterns = patterns('django.views.generic',

#    url(r'^(?P<page>[0-9]+)/$', 'object_list', 
#        dict(comments, paginate_by=25, template_name= 'coltrane/comment_list.html'),
#        name='coltrane_comment_list'),

    url(r'^(?P<page>[0-9]+)/$', 'simple.redirect_to', { 'url': '/ticker/page/1/' },
        name='coltrane_comment_list'),

)
