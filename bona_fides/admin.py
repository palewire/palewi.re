from bona_fides import models
from django.contrib import admin
from adminsortable.admin import SortableAdmin


@admin.register(models.Award)
class AwardAdmin(SortableAdmin):
    list_display = ("title", "url")
    search_fields = ("title",)


@admin.register(models.Clip)
class ClipAdmin(SortableAdmin):
    list_display = ("title", "type", "date", "url")
    list_filter = ("type",)
    search_fields = ("title",)
    date_hierarchy = "date"


@admin.register(models.SocialMediaProfile)
class SocialMediaProfileAdmin(SortableAdmin):
    list_display = ("title", "url")
    search_fields = ("title",)


@admin.register(models.Skill)
class SkillAdmin(SortableAdmin):
    list_display = ("title",)
    search_fields = ("title",)


@admin.register(models.Talk)
class TalkAdmin(SortableAdmin):
    list_display = ("title", "venue", "location", "date")
    search_fields = ("title", "venue")
    date_hierarchy = "date"


@admin.register(models.Doc)
class DocAdmin(SortableAdmin):
    list_display = ("title", "type")
    search_fields = ("title", "description")
    list_filter = ("type",)
