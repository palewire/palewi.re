import models
from django.contrib import admin
from adminsortable.admin import SortableAdmin


class AwardAdmin(SortableAdmin):
    list_display = ("title", "url")
    search_fields = ("title",)


@admin.register(models.Clip)
class ClipAdmin(SortableAdmin):
    list_display = ("title", "url")
    search_fields = ("title",)


class SocialMediaProfileAdmin(SortableAdmin):
    list_display = ("title", "url")
    search_fields = ("title",)


class SkillAdmin(SortableAdmin):
    list_display = ("title",)
    search_fields = ("title",)


admin.site.register(models.Skill, SkillAdmin)
admin.site.register(models.Award, AwardAdmin)
admin.site.register(models.SocialMediaProfile, SocialMediaProfileAdmin)
