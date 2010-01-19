from django.conf.urls.defaults import *
from coltrane.models import Photo
from django.utils.datastructures import SortedDict

favorite_photos = SortedDict({
	'tijuana toilet': {
		'thumbnail': 'http://farm4.static.flickr.com/3126/2759385194_746802b7f4_s.jpg',
		'image': 'http://farm4.static.flickr.com/3126/2759385194_746802b7f4.jpg',
		'url': 'http://www.flickr.com/photos/palewire/2759385194/in/set-72157606698042418/',
	},
	'dead fish': {
		'thumbnail': 'http://farm4.static.flickr.com/3062/2758552851_6da1d80066_s.jpg',
		'image': 'http://farm4.static.flickr.com/3062/2758552851_6da1d80066.jpg',
		'url': 'http://www.flickr.com/photos/palewire/2758552851/in/set-72157606698042418/',
	},
	'goat': {
		'thumbnail': 'http://farm4.static.flickr.com/3490/3918696876_547e3b410a_s.jpg', 
		'image': 'http://farm4.static.flickr.com/3490/3918696876_547e3b410a.jpg',
		'url': 'http://www.flickr.com/photos/palewire/3918696876/in/set-72157622238995029/',
	},
	'orchids': {
		'thumbnail': 'http://farm3.static.flickr.com/2546/3893468451_8a54ae1537_s.jpg',
		'image': 'http://farm3.static.flickr.com/2546/3893468451_8a54ae1537.jpg',
		'url': 'http://www.flickr.com/photos/palewire/3893468451/in/set-72157622148295935/',
	},
	'father and son': {
		'thumbnail': 'http://farm3.static.flickr.com/2398/2765122097_6dedca2d45_s.jpg',
		'image': 'http://farm3.static.flickr.com/2398/2765122097_6dedca2d45.jpg',
		'url': 'http://www.flickr.com/photos/palewire/2765122097/in/set-72157606749555613/'
	},
	'hotwheel': {
		'thumbnail': 'http://farm3.static.flickr.com/2644/3873488316_6ecf2f5ae1_s.jpg',
		'image': 'http://farm3.static.flickr.com/2644/3873488316_6ecf2f5ae1.jpg',
		'url': 'http://www.flickr.com/photos/palewire/3873488316/in/set-72157622067218685/',
	},
	'shooting': {
		'thumbnail': 'http://farm4.static.flickr.com/3660/3604698532_d8252b1f76_s.jpg',
		'image': 'http://farm4.static.flickr.com/3660/3604698532_d8252b1f76.jpg',
		'url': 'http://www.flickr.com/photos/palewire/3604698532/in/set-72157605963630024/',
	},
	'kid': {
		'thumbnail': 'http://farm4.static.flickr.com/3005/2765103643_a213bcee4b_s.jpg',
		'image': 'http://farm4.static.flickr.com/3005/2765103643_a213bcee4b.jpg',
		'url': 'http://www.flickr.com/photos/palewire/2765103643/in/set-72157606749555613/',
	},
	'french toast': {
		'thumbnail': 'http://farm4.static.flickr.com/3652/3661486573_8fd6471a5e_s.jpg',
		'image': 'http://farm4.static.flickr.com/3652/3661486573_8fd6471a5e.jpg',
		'url': 'http://www.flickr.com/photos/palewire/3661486573/in/set-72157621181445341/',
	},
	'eats': {
		'thumbnail': 'http://farm4.static.flickr.com/3351/3582773220_cdaa0628a2_s.jpg',
		'image': 'http://farm4.static.flickr.com/3351/3582773220_cdaa0628a2.jpg',
		'url': 'http://www.flickr.com/photos/palewire/3582773220/in/set-72157619057455478/',
	},
	'war': {
		'thumbnail': 'http://farm4.static.flickr.com/3613/3604688960_46476c015b_s.jpg',
		'image': 'http://farm4.static.flickr.com/3613/3604688960_46476c015b.jpg',
		'url': 'http://www.flickr.com/photos/palewire/3604688960/in/set-72157619394031318/',
	},
	'mona': {
		'thumbnail': 'http://farm4.static.flickr.com/3331/3604670700_992d50f72f_s.jpg',
		'image': 'http://farm4.static.flickr.com/3331/3604670700_992d50f72f.jpg',
		'url': 'http://www.flickr.com/photos/palewire/3604670700/in/set-72157619394031318/',
	},
})

index_dict = {
	'queryset': Photo.objects.all().order_by("-pub_date"),
	'paginate_by': 25,
	'extra_context': dict(favorite_photos=favorite_photos),
}

urlpatterns = patterns('django.views.generic',

	# The root url
	url(r'^$', 'simple.redirect_to', { 'url': '/photos/page/1/', }, name='coltrane_photo_root'),

	# List
	url(r'^page/(?P<page>[0-9]+)/$', 'list_detail.object_list', index_dict, name='coltrane_photo_list'),

)


