from django.db import migrations

LEGACY_CONTENT_TYPES = [
    ("django_comments", None),
    ("coltrane", "category"),
    ("sites", None),
]


def delete_legacy_content_types_and_permissions(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    content_type_ids = set()
    for app_label, model_name in LEGACY_CONTENT_TYPES:
        queryset = ContentType.objects.filter(app_label=app_label)
        if model_name is not None:
            queryset = queryset.filter(model=model_name)
        content_type_ids.update(queryset.values_list("id", flat=True))

    if not content_type_ids:
        return

    Permission.objects.filter(content_type_id__in=content_type_ids).delete()
    ContentType.objects.filter(id__in=content_type_ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("coltrane", "0008_delete_beer_delete_book_delete_commit_delete_link_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                'DROP TABLE IF EXISTS "tagging_taggeditem";',
                'DROP TABLE IF EXISTS "tagging_tag";',
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RemoveField(
            model_name="post",
            name="enable_comments",
        ),
        migrations.RemoveField(
            model_name="post",
            name="categories",
        ),
        migrations.DeleteModel(
            name="Category",
        ),
        migrations.RunPython(delete_legacy_content_types_and_permissions, migrations.RunPython.noop),
        migrations.RunSQL(
            sql="""
DROP TABLE IF EXISTS django_comment_flags;
DROP TABLE IF EXISTS django_comments;
""",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
