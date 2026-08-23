from django.contrib import admin

from bona_fides import models


@admin.register(models.Award)
class AwardAdmin(admin.ModelAdmin):
    list_display = ("title", "url", "year")
    search_fields = ("title",)
    list_filter = ("year",)
    list_editable = ("year",)


@admin.register(models.Clip)
class ClipAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "date", "url")
    list_filter = ("type",)
    search_fields = ("title",)
    date_hierarchy = "date"


@admin.register(models.Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)


@admin.register(models.Talk)
class TalkAdmin(admin.ModelAdmin):
    list_display = ("title", "venue", "location", "date")
    search_fields = ("title", "venue")
    date_hierarchy = "date"


@admin.register(models.Doc)
class DocAdmin(admin.ModelAdmin):
    list_display = ("title", "type")
    search_fields = ("title", "description")
    list_filter = ("type",)
