from django.contrib import admin
from models import Category, Nominee


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("order", "name")

admin.site.register(Category, CategoryAdmin)


class NomineeAdmin(admin.ModelAdmin):
    list_display = ("name", "category")

admin.site.register(Nominee, NomineeAdmin)

