# Admin
from django.contrib import admin

# Models
from tagging.models import Tag
from coltrane.models import *
from django.db.models import get_model

# Custom forms
from coltrane.forms import PostAdminModelForm

class BeerAdmin(admin.ModelAdmin):
    pass
    
admin.site.register(Beer, BeerAdmin)


class BookAdmin(admin.ModelAdmin):
    pass
    
admin.site.register(Book, BookAdmin)


class CommitAdmin(admin.ModelAdmin):
    list_display = ['pub_date', 'repository', 'branch', 'short_message']
    list_filter = ['repository',]
    search_fields = ['message',]
    
admin.site.register(Commit, CommitAdmin)


class TickerAdmin(admin.ModelAdmin):
    pass
    
admin.site.register(Ticker, TickerAdmin)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'post_count',)
    prepopulated_fields = {"slug": ("title",)}
    
admin.site.register(Category, CategoryAdmin)


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
    list_display = ('title', 'pub_date', 'status',)
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ('status', 'pub_date',)
    date_hierarchy = 'pub_date'
    form = PostAdminModelForm

admin.site.register(get_model('coltrane', 'post'), PostAdmin)


class LinkAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Link', {
            'fields': ('title', 'description', 'url', 'pub_date', 'tags'),
            'description': 'About the link.'
        }),
    )
    list_display = ('title', 'pub_date', 'tag_list')
    list_filter = ('pub_date',)
    date_hierarchy = 'pub_date'
    
admin.site.register(Link, LinkAdmin)


class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'pub_date', 'rating')
    list_filter = ('rating',)
    
admin.site.register(Movie, MovieAdmin)


class PhotoAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Photo', {
            'fields': ('title', 'description', 'url', 'pub_date', 'tags'),
            'description': 'About the photo.'
        }),
    )
    list_display = ('title', 'pub_date', 'tag_list')
    list_filter = ('pub_date',)
    date_hierarchy = 'pub_date'
    
admin.site.register(Photo, PhotoAdmin)


class ShoutAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Shout', {
            'fields': ('message', 'url', 'pub_date', 'tags'),
            'description': 'About the shout.'
        }),
    )
    list_display = ('short_message', 'pub_date', 'tag_list')
    list_filter = ('pub_date',)
    date_hierarchy = 'pub_date'
    
admin.site.register(Shout, ShoutAdmin)


class SloganAdmin(admin.ModelAdmin):
    pass
    
admin.site.register(Slogan, SloganAdmin)


class TrackAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Track', {
            'fields': ('artist_name', 'track_name', 'url', 'pub_date', 'track_mbid', 'artist_mbid', 'tags'),
            'description': 'About the track.'
        }),
    )
    list_display = ('artist_name', 'track_name', 'pub_date', 'tag_list')
    search_fields = ('artist_name', 'track_name')
    date_hierarchy = 'pub_date'
    
admin.site.register(Track, TrackAdmin)


class TopDomainAdmin(admin.ModelAdmin):
    list_display = ('name', 'count')
    
admin.site.register(TopDomain, TopDomainAdmin)


class TopTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'count')
    
admin.site.register(TopTag, TopTagAdmin)

