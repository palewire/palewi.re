from coltrane import models
from django.contrib import admin


@admin.register(models.Slogan)
class SloganAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Beer)
@admin.register(models.Book)
@admin.register(models.Link)
@admin.register(models.Photo)
class ThirdPartyBaseAdmin(admin.ModelAdmin):
    """
    Serves as a base for admins for third-party data.
    """
    list_display = ('title', 'pub_date')
    list_filter = ('pub_date',)
    date_hierarchy = 'pub_date'
    search_fields = ['title',]


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'post_count',)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(models.Commit)
class CommitAdmin(ThirdPartyBaseAdmin):
    list_display = ['pub_date', 'repository', 'branch', 'short_message']
    list_filter = ['repository', 'pub_date']
    search_fields = ['message',]


@admin.register(models.Movie)
class MovieAdmin(ThirdPartyBaseAdmin):
    list_display = ('title', 'pub_date', 'rating')
    list_filter = ('rating', 'pub_date',)


@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Post', {
            'fields': ('author', 'pub_date', 'title', 'slug', 'body_markup',),
            'description': 'The post itself.'
        }),
        ('Meta', {
            'fields': ('status', 'repr_image', 'categories', 'enable_comments',),
            'description': 'About the post.'
        }),
    )
    list_display = ('title', 'pub_date', 'status', 'enable_comments',)
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ('status', 'enable_comments', 'pub_date',)
    date_hierarchy = 'pub_date'
    save_on_top = True
    list_editable = ("status", 'enable_comments',)


@admin.register(models.Shout)
class ShoutAdmin(ThirdPartyBaseAdmin):
    list_display = ('short_message', 'pub_date')
    search_fields = ['message',]


@admin.register(models.Ticker)
class TickerAdmin(ThirdPartyBaseAdmin):
    list_display = ['__str__', 'pub_date']
    search_fields = []


@admin.register(models.Track)
class TrackAdmin(ThirdPartyBaseAdmin):
    list_display = ('artist_name', 'track_name', 'pub_date')
    search_fields = ('artist_name', 'track_name')
