from django.contrib import admin
from coltrane.models import *


class ThirdPartyBaseAdmin(admin.ModelAdmin):
    """
    Serves as a base for admins for third-party data.
    """
    list_display = ('title', 'pub_date')
    list_filter = ('pub_date',)
    date_hierarchy = 'pub_date'
    search_fields = ['title',]


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'post_count',)
    prepopulated_fields = {"slug": ("title",)}


class CommitAdmin(ThirdPartyBaseAdmin):
    list_display = ['pub_date', 'repository', 'branch', 'short_message']
    list_filter = ['repository', 'pub_date']
    search_fields = ['message',]


class MovieAdmin(ThirdPartyBaseAdmin):
    list_display = ('title', 'pub_date', 'rating')
    list_filter = ('rating', 'pub_date',)


class PostAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Post', {
            'fields': ('author', 'pub_date', 'title', 'slug', 'body_markup',),
            'description': 'The post itself.'
        }),
        ('Meta', {
            'fields': ('status', 'categories', 'tags', 'enable_comments',),
            'description': 'About the post.'
        }),
    )
    list_display = ('title', 'pub_date', 'status', 'enable_comments',)
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ('status', 'enable_comments', 'pub_date',)
    date_hierarchy = 'pub_date'
    save_on_top = True
    list_editable = ("status", 'enable_comments',)


class ShoutAdmin(ThirdPartyBaseAdmin):
    list_display = ('short_message', 'pub_date')
    search_fields = ['message',]


class TickerAdmin(ThirdPartyBaseAdmin):
    list_display = ['__unicode__', 'pub_date']
    search_fields = []


class TrackAdmin(ThirdPartyBaseAdmin):
    list_display = ('artist_name', 'track_name', 'pub_date')
    search_fields = ('artist_name', 'track_name')


admin.site.register(Beer, ThirdPartyBaseAdmin)
admin.site.register(Book, ThirdPartyBaseAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Commit, CommitAdmin)
admin.site.register(Link, ThirdPartyBaseAdmin)
admin.site.register(Movie, MovieAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Photo, ThirdPartyBaseAdmin)
admin.site.register(Shout, ShoutAdmin)
admin.site.register(Slogan, admin.ModelAdmin)
admin.site.register(Ticker, TickerAdmin)
admin.site.register(Track, TrackAdmin)
