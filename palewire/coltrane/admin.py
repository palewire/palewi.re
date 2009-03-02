from django.contrib import admin
from models import Category, Photo, Post, Link, Slogan, Tumbler, Track, Tweet, Video

class CategoryAdmin(admin.ModelAdmin):
	prepopulated_fields = {"slug": ("title",)}
	
admin.site.register(Category, CategoryAdmin)


class PostAdmin(admin.ModelAdmin):
	list_display = ('title', 'pub_date',)
	prepopulated_fields = {"slug": ("title",)}
	
admin.site.register(Post, PostAdmin)


class LinkAdmin(admin.ModelAdmin):
	prepopulated_fields = {"slug": ("title",)}
	
admin.site.register(Link, LinkAdmin)


class TweetAdmin(admin.ModelAdmin):
	prepopulated_fields = {"slug": ("body",)}
	
admin.site.register(Tweet, TweetAdmin)


class PhotoAdmin(admin.ModelAdmin):
	prepopulated_fields = {"slug": ("title",)}
	
admin.site.register(Photo, PhotoAdmin)


class VideoAdmin(admin.ModelAdmin):
	prepopulated_fields = {"slug": ("title",)}
	
admin.site.register(Video, VideoAdmin)


class TumblerAdmin(admin.ModelAdmin):
	pass
	
admin.site.register(Tumbler, TumblerAdmin)


class TrackAdmin(admin.ModelAdmin):
	pass
	
admin.site.register(Track, TrackAdmin)


class SloganAdmin(admin.ModelAdmin):
	pass
	
admin.site.register(Slogan, SloganAdmin)