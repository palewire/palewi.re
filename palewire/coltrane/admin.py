from django.contrib import admin
from models import Category, Feature, Photo, Post, Link, Slogan, Ticker, Track, Shout, Video

class CategoryAdmin(admin.ModelAdmin):
	list_display = ('title', 'post_count',)
	prepopulated_fields = {"slug": ("title",)}
	
admin.site.register(Category, CategoryAdmin)


class PostAdmin(admin.ModelAdmin):
	list_display = ('title', 'pub_date', 'status',)
	prepopulated_fields = {"slug": ("title",)}
	list_filter = ('status', 'pub_date',)
	date_hierarchy = 'pub_date'
	
admin.site.register(Post, PostAdmin)


class LinkAdmin(admin.ModelAdmin):
	prepopulated_fields = {"slug": ("title",)}
	
admin.site.register(Link, LinkAdmin)


class ShoutAdmin(admin.ModelAdmin):
	prepopulated_fields = {"slug": ("body",)}
	
admin.site.register(Shout, ShoutAdmin)


class PhotoAdmin(admin.ModelAdmin):
	prepopulated_fields = {"slug": ("title",)}
	
admin.site.register(Photo, PhotoAdmin)


class VideoAdmin(admin.ModelAdmin):
	prepopulated_fields = {"slug": ("title",)}
	
admin.site.register(Video, VideoAdmin)


class TickerAdmin(admin.ModelAdmin):
	pass
	
admin.site.register(Ticker, TickerAdmin)


class FeatureAdmin(admin.ModelAdmin):
	pass
	
admin.site.register(Feature, FeatureAdmin)


class TrackAdmin(admin.ModelAdmin):
	pass
	
admin.site.register(Track, TrackAdmin)


class SloganAdmin(admin.ModelAdmin):
	pass
	
admin.site.register(Slogan, SloganAdmin)