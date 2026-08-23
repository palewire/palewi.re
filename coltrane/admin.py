from django.contrib import admin

from coltrane import models


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "post_count",
    )
    prepopulated_fields = {"slug": ("title",)}


@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Post",
            {
                "fields": (
                    "author",
                    "pub_date",
                    "title",
                    "slug",
                    "body_markup",
                ),
                "description": "The post itself.",
            },
        ),
        (
            "Meta",
            {
                "fields": (
                    "status",
                    "repr_image",
                    "categories",
                    "enable_comments",
                ),
                "description": "About the post.",
            },
        ),
    )
    list_display = (
        "title",
        "pub_date",
        "status",
        "enable_comments",
    )
    prepopulated_fields = {"slug": ("title",)}
    list_filter = (
        "status",
        "enable_comments",
        "pub_date",
    )
    date_hierarchy = "pub_date"
    save_on_top = True
    list_editable = (
        "status",
        "enable_comments",
    )
