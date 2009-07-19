from django.contrib import admin
from tagging.models import Tag
from coltrane.models import Category, Photo, Post, Link, Slogan, Ticker, Track, Shout
from django.db.models import get_model
from coltrane.forms import PostAdminModelForm

class PostAdmin(admin.ModelAdmin):
	list_display = ('title', 'pub_date', 'status',)
	prepopulated_fields = {"slug": ("title",)}
	list_filter = ('status', 'pub_date',)
	date_hierarchy = 'pub_date'
	form = PostAdminModelForm

admin.site.register(get_model('coltrane', 'post'), PostAdmin)


class CategoryAdmin(admin.ModelAdmin):
	list_display = ('title', 'post_count',)
	prepopulated_fields = {"slug": ("title",)}
	
admin.site.register(Category, CategoryAdmin)


class LinkAdmin(admin.ModelAdmin):
	pass
	
admin.site.register(Link, LinkAdmin)


class ShoutAdmin(admin.ModelAdmin):
	pass
	
admin.site.register(Shout, ShoutAdmin)


class PhotoAdmin(admin.ModelAdmin):
	prepopulated_fields = {"slug": ("title",)}
	
admin.site.register(Photo, PhotoAdmin)


class TickerAdmin(admin.ModelAdmin):
	pass
	
admin.site.register(Ticker, TickerAdmin)


class TrackAdmin(admin.ModelAdmin):
	pass
	
admin.site.register(Track, TrackAdmin)


class SloganAdmin(admin.ModelAdmin):
	pass
	
admin.site.register(Slogan, SloganAdmin)