import models
from django.contrib import admin
from adminsortable.admin import SortableAdmin


class SocialMediaProfileAdmin(SortableAdmin):
    list_display = ("title", "url")
    search_fields = ("title",)


admin.site.register(models.SocialMediaProfile, SocialMediaProfileAdmin)
