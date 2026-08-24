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


# ---------------------------------------------------------------------------
# Tests for migration 0010 – retire Sites, flatpages, robots, content tables
# ---------------------------------------------------------------------------

MIGRATION_0010 = ("coltrane", "0010_retire_sites_flatpages_robots_tables")

# Content types that belong only to the apps being retired in 0010
RETIRED_0010_CONTENT_TYPES = {
    ("correx", "change"),
    ("correx", "changetype"),
    ("flatpages", "flatpage"),
    ("robots", "rule"),
    ("robots", "url"),
}

# Content types that must still exist after 0010
PRESERVED_0010_CONTENT_TYPES = {
    ("coltrane", "post"),
    ("auth", "user"),
}

# Complete FK topology for the 10 tables (mirrors production schema).
_CREATE_SITES_TOPOLOGY = """
CREATE TABLE django_site (
    id   integer PRIMARY KEY,
    domain varchar(100) NOT NULL,
    name   varchar(50)  NOT NULL
);

CREATE TABLE django_content_changetype (
    name         varchar(50) PRIMARY KEY,
    slug         varchar(50) NOT NULL,
    description  text        NOT NULL DEFAULT '',
    change_count integer     NOT NULL DEFAULT 0
);

CREATE TABLE django_content_changelog (
    id              serial  PRIMARY KEY,
    description     text    NOT NULL DEFAULT '',
    change_type_id  varchar(50) REFERENCES django_content_changetype(name),
    pub_date        timestamp,
    is_public       boolean NOT NULL DEFAULT true,
    user_id         integer REFERENCES auth_user(id),
    site_id         integer NOT NULL REFERENCES django_site(id),
    content_app     varchar(100) NOT NULL DEFAULT '',
    content_type_id integer REFERENCES django_content_type(id),
    object_id       integer
);

CREATE TABLE django_flatpage (
    id                    serial  PRIMARY KEY,
    url                   varchar(100) NOT NULL,
    title                 varchar(200) NOT NULL,
    content               text    NOT NULL DEFAULT '',
    enable_comments       boolean NOT NULL DEFAULT false,
    template_name         varchar(70) NOT NULL DEFAULT '',
    registration_required boolean NOT NULL DEFAULT false
);

CREATE TABLE django_flatpage_sites (
    id          serial  PRIMARY KEY,
    flatpage_id integer NOT NULL REFERENCES django_flatpage(id),
    site_id     integer NOT NULL REFERENCES django_site(id)
);

CREATE TABLE robots_url (
    id      serial  PRIMARY KEY,
    pattern varchar(255) NOT NULL
);

CREATE TABLE robots_rule (
    id          serial  PRIMARY KEY,
    robot       varchar(255) NOT NULL,
    crawl_delay numeric
);

CREATE TABLE robots_rule_allowed (
    id      serial  PRIMARY KEY,
    rule_id integer NOT NULL REFERENCES robots_rule(id),
    url_id  integer NOT NULL REFERENCES robots_url(id)
);

CREATE TABLE robots_rule_disallowed (
    id      serial  PRIMARY KEY,
    rule_id integer NOT NULL REFERENCES robots_rule(id),
    url_id  integer NOT NULL REFERENCES robots_url(id)
);

CREATE TABLE robots_rule_sites (
    id      serial  PRIMARY KEY,
    rule_id integer NOT NULL REFERENCES robots_rule(id),
    site_id integer NOT NULL REFERENCES django_site(id)
);
"""

_DROP_SITES_TOPOLOGY = """
DROP TABLE IF EXISTS django_content_changelog;
DROP TABLE IF EXISTS django_flatpage_sites;
DROP TABLE IF EXISTS robots_rule_allowed;
DROP TABLE IF EXISTS robots_rule_disallowed;
DROP TABLE IF EXISTS robots_rule_sites;
DROP TABLE IF EXISTS django_content_changetype;
DROP TABLE IF EXISTS django_flatpage;
DROP TABLE IF EXISTS robots_rule;
DROP TABLE IF EXISTS robots_url;
DROP TABLE IF EXISTS django_site;
"""

_RETIRED_TABLES = [
    "django_site",
    "django_content_changelog",
    "django_content_changetype",
    "django_flatpage",
    "django_flatpage_sites",
    "robots_rule",
    "robots_rule_allowed",
    "robots_rule_disallowed",
    "robots_rule_sites",
    "robots_url",
]


def _seed_retired_content_types(apps):
    """Insert content type + permission rows for the apps being retired."""
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    ids: set[int] = set()
    for app_label, model in RETIRED_0010_CONTENT_TYPES | PRESERVED_0010_CONTENT_TYPES:
        ct, _ = ContentType.objects.get_or_create(app_label=app_label, model=model)
        Permission.objects.get_or_create(
            content_type_id=ct.id,
            codename=f"view_{app_label}_{model}",
            defaults={"name": f"Can view {app_label}.{model}"},
        )
        ids.add(ct.id)
    return ids


def _create_sites_topology():
    """Reconstruct the production FK topology for the 10 legacy tables."""
    with connection.cursor() as cursor:
        cursor.execute(_CREATE_SITES_TOPOLOGY)
        # Insert one representative row per leaf-table group
        cursor.execute("INSERT INTO django_site VALUES (1, 'example.com', 'Example')")
        cursor.execute("INSERT INTO django_content_changetype VALUES ('edit', 'edit', 'An edit', 0)")
        cursor.execute("INSERT INTO django_flatpage VALUES (1, '/about/', 'About', '', false, '', false)")
        cursor.execute("INSERT INTO robots_url VALUES (1, '/private/')")
        cursor.execute("INSERT INTO robots_rule VALUES (1, '*', NULL)")
        # FK leaf rows
        cursor.execute("INSERT INTO django_flatpage_sites VALUES (1, 1, 1)")
        cursor.execute("INSERT INTO robots_rule_sites VALUES (1, 1, 1)")
        cursor.execute("INSERT INTO robots_rule_allowed VALUES (1, 1, 1)")
        cursor.execute("INSERT INTO robots_rule_disallowed VALUES (1, 1, 1)")


def _drop_sites_topology():
    with connection.cursor() as cursor:
        cursor.execute(_DROP_SITES_TOPOLOGY)


def _assert_tables_removed():
    tables = set(connection.introspection.table_names())
    for table in _RETIRED_TABLES:
        assert table not in tables, f"Table {table!r} should have been removed by 0010"


def _assert_unrelated_tables_preserved():
    tables = set(connection.introspection.table_names())
    for table in ("coltrane_post", "coltrane_slogan", "auth_user", "django_content_type"):
        assert table in tables, f"Table {table!r} should have been preserved by 0010"


def _assert_content_types_removed_and_preserved(apps):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    existing = set(ContentType.objects.values_list("app_label", "model"))

    assert RETIRED_0010_CONTENT_TYPES.isdisjoint(existing), "Retired content types should have been removed"
    assert PRESERVED_0010_CONTENT_TYPES <= existing, "Current-app content types should be preserved"

    removed_perms = Permission.objects.filter(codename__in={f"view_{a}_{m}" for a, m in RETIRED_0010_CONTENT_TYPES})
    assert not removed_perms.exists(), "Permissions for retired apps should be removed"

    preserved_perms = Permission.objects.filter(codename__in={f"view_{a}_{m}" for a, m in PRESERVED_0010_CONTENT_TYPES})
    assert preserved_perms.count() == len(PRESERVED_0010_CONTENT_TYPES), (
        "Permissions for current apps should be preserved"
    )


@pytest.mark.django_db(transaction=True)
def test_migration_0010_removes_all_legacy_tables_with_full_topology():
    """Migration 0010 drops all 10 legacy tables when they exist with FK data."""
    apps = _migrate_to(MIGRATION_0009)
    try:
        _create_sites_topology()
        _seed_retired_content_types(apps)

        apps = _migrate_to(MIGRATION_0010)

        _assert_tables_removed()
        _assert_unrelated_tables_preserved()
        _assert_content_types_removed_and_preserved(apps)
    finally:
        _drop_sites_topology()
        _migrate_to(MIGRATION_0010)


@pytest.mark.django_db(transaction=True)
def test_migration_0010_is_idempotent_on_fresh_database():
    """Migration 0010 succeeds even when legacy tables do not exist (fresh DB)."""
    apps = _migrate_to(MIGRATION_0009)
    # Do NOT create the legacy tables — simulate a fresh database.

    # Seed only the preserved content types (no retired ones).
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    for app_label, model in PRESERVED_0010_CONTENT_TYPES:
        ct, _ = ContentType.objects.get_or_create(app_label=app_label, model=model)
        Permission.objects.get_or_create(
            content_type_id=ct.id,
            codename=f"view_{app_label}_{model}",
            defaults={"name": f"Can view {app_label}.{model}"},
        )

    apps = _migrate_to(MIGRATION_0010)

    _assert_tables_removed()
    _assert_unrelated_tables_preserved()
    # Only preserved types were seeded; none of them should be gone.
    existing = set(ContentType.objects.values_list("app_label", "model"))
    assert PRESERVED_0010_CONTENT_TYPES <= existing
