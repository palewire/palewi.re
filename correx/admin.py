# Admin
from django.contrib import admin

# Models
from correx.models import Change, ChangeType


class ChangeTypeAdmin(admin.ModelAdmin):
	list_display = ('name', 'description', 'change_count',)
	prepopulated_fields = {"slug": ("name",)}


class ChangeAdmin(admin.ModelAdmin):
	list_display = ('get_short_description', 'pub_date', 'change_type', 'user', 'site', 'content_app', 'content_type', 'get_content_object', 'is_public',)
	search_fields = ['description', 'user', 'site', 'content_type', 'content_type', 'change_type']
	list_filter = ('change_type', 'site', 'content_app', 'is_public',)
	date_hierarchy = 'pub_date'
	fieldsets = (
		('Editorial', { 'fields': ('pub_date', 'change_type', 'description',)}),
		('Meta', { 'fields': ('user', 'site', 'content_app', 'content_type', 'object_id',)}),
		('Publishing', { 'fields': ('is_public',)}),
	)


# Register admins
admin.site.register(ChangeType, ChangeTypeAdmin)
admin.site.register(Change, ChangeAdmin)