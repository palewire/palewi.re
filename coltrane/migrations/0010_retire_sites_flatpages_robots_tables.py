"""
Remove legacy Django Sites, flatpages, robots, and django-content tables.

Background
----------
These tables are residual schema from third-party apps (django.contrib.sites,
django.contrib.flatpages, django-robots, django-content) that were removed from
INSTALLED_APPS in earlier work.  None of these apps appear in INSTALLED_APPS,
none of the tables have any data rows, and no current code references them.

Migration 0009 preserved ``django_site`` because other tables still referenced
it via foreign keys.  This migration removes those dependent tables first, then
removes ``django_site`` and the remaining orphan parents.

WARNING: This migration is irreversible and permanently deletes schema.
Data was audited and archived to palewire/palewi.re-archive at tag
v2026-08-24-sites-legacy before deletion.  All 10 tables contained 0 rows.

Deletion order (leaf → parent to avoid FK violations)
------------------------------------------------------
1. django_content_changelog  (refs changetype, django_content_type, site, user)
2. django_flatpage_sites      (refs flatpage, site)
3. robots_rule_sites          (refs rule, site)
4. robots_rule_allowed        (refs rule, url)
5. robots_rule_disallowed     (refs rule, url)
6. django_content_changetype  (parent of changelog)
7. django_flatpage            (parent of flatpage_sites)
8. robots_rule                (parent of rule_sites, rule_allowed, rule_disallowed)
9. robots_url                 (parent of rule_allowed, rule_disallowed)
10. django_site               (referenced by all three FK groups above)
"""

from django.db import migrations

# Content types / permissions associated only with the removed apps.
# app_label=None means delete all content types for that app label.
LEGACY_CONTENT_TYPES = [
    ("correx", None),  # django_content_changelog / django_content_changetype
    ("flatpages", None),  # django_flatpage
    ("robots", None),  # robots_rule, robots_url
]


def delete_legacy_content_types_and_permissions(apps, schema_editor):
    """Remove stale content-type and permission rows for deleted apps."""
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")

    content_type_ids: set[int] = set()
    for app_label, model_name in LEGACY_CONTENT_TYPES:
        qs = ContentType.objects.filter(app_label=app_label)
        if model_name is not None:
            qs = qs.filter(model=model_name)
        content_type_ids.update(qs.values_list("id", flat=True))

    if not content_type_ids:
        return

    Permission.objects.filter(content_type_id__in=content_type_ids).delete()
    ContentType.objects.filter(id__in=content_type_ids).delete()


class Migration(migrations.Migration):
    """Retire legacy Sites, flatpages, robots, and django-content tables."""

    dependencies = [
        ("coltrane", "0009_remove_legacy_comments_categories_sites"),
    ]

    operations = [
        # Step 1: Remove content types / permissions for the retiring apps.
        # Done first so no FK from Permission → ContentType blocks table drops.
        migrations.RunPython(
            delete_legacy_content_types_and_permissions,
            reverse_code=migrations.RunPython.noop,
        ),
        # Step 2: Drop tables in leaf-to-parent order.
        # Each DROP uses IF EXISTS so the migration is idempotent on both a
        # production database (tables exist) and a fresh database (tables do
        # not exist because no app ever created them in this Django project).
        migrations.RunSQL(
            sql="""
-- Leaf tables that reference django_site --------------------------------
DROP TABLE IF EXISTS "django_content_changelog";
DROP TABLE IF EXISTS "django_flatpage_sites";
DROP TABLE IF EXISTS "robots_rule_sites";

-- Leaf join tables for robots -----------------------------------------
DROP TABLE IF EXISTS "robots_rule_allowed";
DROP TABLE IF EXISTS "robots_rule_disallowed";

-- Parent tables -------------------------------------------------------
DROP TABLE IF EXISTS "django_content_changetype";
DROP TABLE IF EXISTS "django_flatpage";
DROP TABLE IF EXISTS "robots_rule";
DROP TABLE IF EXISTS "robots_url";

-- Root table ----------------------------------------------------------
DROP TABLE IF EXISTS "django_site";
""",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
