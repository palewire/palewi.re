"""Regression tests for production-shaped migration paths."""

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

MIGRATION_0007 = ("coltrane", "0007_remove_slogan_state")
MIGRATION_0008 = ("coltrane", "0008_delete_beer_delete_book_delete_commit_delete_link_and_more")
MIGRATION_0009 = ("coltrane", "0009_remove_legacy_comments_categories_sites")

REMOVED_CONTENT_TYPES = {
    ("coltrane", "category"),
    ("coltrane", "track"),
    ("django_comments", "comment"),
    ("django_comments", "commentflag"),
    ("sites", "site"),
}
PRESERVED_CONTENT_TYPES = {
    ("coltrane", "post"),
    ("other", "site"),
}


def _migrate_to(target):
    executor = MigrationExecutor(connection)
    targets = [
        target,
        *executor.loader.graph.leaf_nodes("auth"),
        *executor.loader.graph.leaf_nodes("contenttypes"),
    ]
    executor.migrate(targets)
    return executor.loader.project_state(targets).apps


def _seed_content_types(apps, *, include_track=True):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")

    content_types = {}
    content_type_keys = REMOVED_CONTENT_TYPES | PRESERVED_CONTENT_TYPES
    if not include_track:
        content_type_keys = content_type_keys - {("coltrane", "track")}

    for app_label, model in content_type_keys:
        content_type, _ = ContentType.objects.get_or_create(app_label=app_label, model=model)
        Permission.objects.get_or_create(
            content_type_id=content_type.id,
            codename=f"view_{app_label}_{model}",
            defaults={"name": f"Can view {app_label}.{model}"},
        )
        content_types[(app_label, model)] = content_type
    return content_types


def _create_legacy_tagging_tables(content_types):
    tagged_content_type = content_types.get(("coltrane", "track"), content_types[("coltrane", "post")])
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE tagging_tag (
                id integer PRIMARY KEY,
                name varchar(50) NOT NULL UNIQUE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE tagging_taggeditem (
                id integer PRIMARY KEY,
                tag_id integer NOT NULL REFERENCES tagging_tag(id),
                content_type_id integer NOT NULL REFERENCES django_content_type(id),
                object_id integer NOT NULL
            )
            """
        )
        cursor.execute("INSERT INTO tagging_tag (id, name) VALUES (1, 'legacy')")
        cursor.execute(
            """
            INSERT INTO tagging_taggeditem (id, tag_id, content_type_id, object_id)
            VALUES (1, 1, %s, 101), (2, 1, %s, 102)
            """,
            [
                tagged_content_type.id,
                content_types[("coltrane", "post")].id,
            ],
        )


def _create_legacy_sites_tables():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE django_site (
                id integer PRIMARY KEY,
                domain varchar(100) NOT NULL,
                name varchar(50) NOT NULL
            )
            """
        )
        cursor.execute("INSERT INTO django_site (id, domain, name) VALUES (1, 'example.com', 'Example')")

        for table_name in ("django_content_changelog", "django_flatpage_sites", "robots_rule_sites"):
            cursor.execute(
                f"""
                CREATE TABLE {table_name} (
                    id integer PRIMARY KEY,
                    site_id integer NOT NULL REFERENCES django_site(id)
                )
                """
            )
            cursor.execute(f"INSERT INTO {table_name} (id, site_id) VALUES (1, 1)")


def _assert_legacy_sites_preserved():
    with connection.cursor() as cursor:
        for table_name in (
            "django_site",
            "django_content_changelog",
            "django_flatpage_sites",
            "robots_rule_sites",
        ):
            cursor.execute(f"SELECT count(*) FROM {table_name}")
            assert cursor.fetchone() == (1,)

        cursor.execute(
            """
            SELECT count(*)
            FROM pg_constraint
            WHERE contype = 'f'
              AND confrelid = 'django_site'::regclass
              AND conrelid IN (
                  'django_content_changelog'::regclass,
                  'django_flatpage_sites'::regclass,
                  'robots_rule_sites'::regclass
              )
            """
        )
        assert cursor.fetchone() == (3,)


def _drop_legacy_sites_tables():
    with connection.cursor() as cursor:
        for table_name in ("django_content_changelog", "django_flatpage_sites", "robots_rule_sites", "django_site"):
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")


def _assert_cleanup(apps):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    existing_content_types = set(ContentType.objects.values_list("app_label", "model"))

    assert REMOVED_CONTENT_TYPES.isdisjoint(existing_content_types)
    assert PRESERVED_CONTENT_TYPES <= existing_content_types

    removed_permissions = Permission.objects.filter(
        codename__in={f"view_{app_label}_{model}" for app_label, model in REMOVED_CONTENT_TYPES}
    )
    preserved_permissions = Permission.objects.filter(
        codename__in={f"view_{app_label}_{model}" for app_label, model in PRESERVED_CONTENT_TYPES}
    )
    assert not removed_permissions.exists()
    assert preserved_permissions.count() == len(PRESERVED_CONTENT_TYPES)

    tables = set(connection.introspection.table_names())
    assert "tagging_taggeditem" not in tables
    assert "tagging_tag" not in tables


@pytest.mark.django_db(transaction=True)
def test_migrations_remove_production_legacy_tagging_tables():
    apps = _migrate_to(MIGRATION_0007)
    try:
        content_types = _seed_content_types(apps)
        _create_legacy_tagging_tables(content_types)

        apps = _migrate_to(MIGRATION_0009)

        _assert_cleanup(apps)
    finally:
        _migrate_to(MIGRATION_0009)


@pytest.mark.django_db(transaction=True)
def test_migration_0009_cleans_tagging_tables_left_after_0008():
    apps = _migrate_to(MIGRATION_0008)
    try:
        content_types = _seed_content_types(apps, include_track=False)
        _create_legacy_tagging_tables(content_types)
        _create_legacy_sites_tables()

        apps = _migrate_to(MIGRATION_0009)

        _assert_cleanup(apps)
        _assert_legacy_sites_preserved()
    finally:
        _drop_legacy_sites_tables()
        _migrate_to(MIGRATION_0009)
