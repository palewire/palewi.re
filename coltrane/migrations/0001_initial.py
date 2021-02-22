# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings

# import tagging.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        # ('tagging', '__first__'),
        ("contenttypes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Beer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("url", models.URLField(max_length=1000)),
                (
                    "pub_date",
                    models.DateTimeField(
                        default=datetime.datetime.now, verbose_name="publication date"
                    ),
                ),
                # ('tags', tagging.fields.TagField(help_text='Separate tags with spaces.', max_length=1000, blank=True)),
                ("title", models.CharField(max_length=250, null=True, blank=True)),
                ("brewery", models.CharField(max_length=250)),
            ],
            options={
                "ordering": ("-pub_date",),
                "abstract": False,
                "get_latest_by": "pub_date",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Book",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("url", models.URLField(max_length=1000)),
                (
                    "pub_date",
                    models.DateTimeField(
                        default=datetime.datetime.now, verbose_name="publication date"
                    ),
                ),
                # ('tags', tagging.fields.TagField(help_text='Separate tags with spaces.', max_length=1000, blank=True)),
                ("isbn", models.CharField(unique=True, max_length=20)),
                ("title", models.CharField(max_length=250)),
                ("authors", models.CharField(max_length=250, null=True, blank=True)),
            ],
            options={
                "ordering": ("-pub_date",),
                "abstract": False,
                "get_latest_by": "pub_date",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        help_text="Maximum 250 characters.", max_length=250
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="Suggested value automatically generated from title. Must be unique.",
                        unique=True,
                    ),
                ),
                ("description", models.TextField(null=True, blank=True)),
                ("post_count", models.IntegerField(default=0, editable=False)),
            ],
            options={
                "ordering": ["title"],
                "verbose_name_plural": "Categories",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Commit",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("url", models.URLField(max_length=1000)),
                (
                    "pub_date",
                    models.DateTimeField(
                        default=datetime.datetime.now, verbose_name="publication date"
                    ),
                ),
                # ('tags', tagging.fields.TagField(help_text='Separate tags with spaces.', max_length=1000, blank=True)),
                ("repository", models.CharField(max_length=100)),
                ("branch", models.CharField(max_length=100, blank=True)),
                ("message", models.TextField()),
            ],
            options={
                "ordering": ("-pub_date",),
                "abstract": False,
                "get_latest_by": "pub_date",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Link",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("url", models.URLField(max_length=1000)),
                (
                    "pub_date",
                    models.DateTimeField(
                        default=datetime.datetime.now, verbose_name="publication date"
                    ),
                ),
                # ('tags', tagging.fields.TagField(help_text='Separate tags with spaces.', max_length=1000, blank=True)),
                ("title", models.CharField(max_length=250)),
                ("description", models.TextField(null=True, blank=True)),
            ],
            options={
                "ordering": ("-pub_date",),
                "abstract": False,
                "get_latest_by": "pub_date",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Location",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("url", models.URLField(max_length=1000)),
                (
                    "pub_date",
                    models.DateTimeField(
                        default=datetime.datetime.now, verbose_name="publication date"
                    ),
                ),
                # ('tags', tagging.fields.TagField(help_text='Separate tags with spaces.', max_length=1000, blank=True)),
                ("title", models.CharField(max_length=250)),
                ("description", models.TextField(null=True, blank=True)),
                ("latitude", models.FloatField(null=True)),
                ("longitude", models.FloatField(null=True)),
            ],
            options={
                "ordering": ("-pub_date",),
                "abstract": False,
                "get_latest_by": "pub_date",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Movie",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("url", models.URLField(max_length=1000)),
                (
                    "pub_date",
                    models.DateTimeField(
                        default=datetime.datetime.now, verbose_name="publication date"
                    ),
                ),
                # ('tags', tagging.fields.TagField(help_text='Separate tags with spaces.', max_length=1000, blank=True)),
                ("title", models.CharField(max_length=250, null=True, blank=True)),
                (
                    "rating",
                    models.FloatField(
                        null=True, verbose_name=b"One to five star rating.", blank=True
                    ),
                ),
            ],
            options={
                "ordering": ("-pub_date",),
                "abstract": False,
                "get_latest_by": "pub_date",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Photo",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("url", models.URLField(max_length=1000)),
                (
                    "pub_date",
                    models.DateTimeField(
                        default=datetime.datetime.now, verbose_name="publication date"
                    ),
                ),
                # ('tags', tagging.fields.TagField(help_text='Separate tags with spaces.', max_length=1000, blank=True)),
                ("title", models.CharField(max_length=250, null=True, blank=True)),
                ("description", models.TextField(null=True, blank=True)),
            ],
            options={
                "ordering": ("-pub_date",),
                "abstract": False,
                "get_latest_by": "pub_date",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Post",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "wordpress_id",
                    models.IntegerField(
                        help_text="The junky old wp_posts id from before the migration",
                        unique=True,
                        null=True,
                        editable=False,
                        blank=True,
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        help_text="Maximum 250 characters.", max_length=250
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="Suggested value automatically generated from title.",
                        max_length=300,
                        unique_for_date=b"pub_date",
                    ),
                ),
                (
                    "body_markup",
                    models.TextField(
                        help_text="The HTML of the post that is edited by the author."
                    ),
                ),
                (
                    "body_html",
                    models.TextField(
                        help_text="The HTML of the post run through Pygments.",
                        null=True,
                        editable=False,
                        blank=True,
                    ),
                ),
                (
                    "pub_date",
                    models.DateTimeField(
                        default=datetime.datetime.now, verbose_name="publication date"
                    ),
                ),
                ("enable_comments", models.BooleanField(default=True)),
                (
                    "status",
                    models.IntegerField(
                        default=1,
                        help_text="Only 'Live' entries will be publicly displayed.",
                        choices=[(1, b"Live"), (2, b"Draft"), (3, b"Hidden")],
                    ),
                ),
                # ('tags', tagging.fields.TagField(help_text='Separate tags with spaces.', max_length=255, blank=True)),
                (
                    "author",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
                ("categories", models.ManyToManyField(to="coltrane.Category")),
            ],
            options={
                "ordering": ["-pub_date"],
                "get_latest_by": "pub_date",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Shout",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("url", models.URLField(max_length=1000)),
                (
                    "pub_date",
                    models.DateTimeField(
                        default=datetime.datetime.now, verbose_name="publication date"
                    ),
                ),
                # ('tags', tagging.fields.TagField(help_text='Separate tags with spaces.', max_length=1000, blank=True)),
                ("message", models.TextField(max_length=140)),
            ],
            options={
                "ordering": ("-pub_date",),
                "abstract": False,
                "get_latest_by": "pub_date",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Slogan",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        help_text="Maximum 250 characters.", max_length=250
                    ),
                ),
            ],
            options={
                "ordering": ["title"],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Ticker",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("object_id", models.PositiveIntegerField()),
                ("pub_date", models.DateTimeField()),
                (
                    "content_type",
                    models.ForeignKey(
                        to="contenttypes.ContentType", on_delete=models.CASCADE
                    ),
                ),
            ],
            options={
                "ordering": ("-pub_date",),
                "verbose_name_plural": "Ticker",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TopDomain",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(unique=True, max_length=50, verbose_name="name"),
                ),
                ("count", models.IntegerField()),
                (
                    "stratum",
                    models.IntegerField(
                        help_text=b"The font-size stratum to stick         this guy in when puffing up the cloud."
                    ),
                ),
            ],
            options={
                "ordering": ("-count", "name"),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TopTag",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(unique=True, max_length=50, verbose_name="name"),
                ),
                ("count", models.IntegerField()),
                (
                    "stratum",
                    models.IntegerField(
                        help_text=b"The font-size stratum to stick         this guy in when puffing up the cloud."
                    ),
                ),
                # ('tag', models.OneToOneField(to='tagging.Tag')),
            ],
            options={
                "ordering": ("-count", "name"),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Track",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("url", models.URLField(max_length=1000)),
                (
                    "pub_date",
                    models.DateTimeField(
                        default=datetime.datetime.now, verbose_name="publication date"
                    ),
                ),
                # ('tags', tagging.fields.TagField(help_text='Separate tags with spaces.', max_length=1000, blank=True)),
                ("artist_name", models.CharField(max_length=250)),
                ("track_name", models.CharField(max_length=250)),
                (
                    "track_mbid",
                    models.CharField(
                        max_length=36, verbose_name="MusicBrainz Track ID", blank=True
                    ),
                ),
                (
                    "artist_mbid",
                    models.CharField(
                        max_length=36, verbose_name="MusicBrainz Artist ID", blank=True
                    ),
                ),
            ],
            options={
                "ordering": ("-pub_date",),
                "abstract": False,
                "get_latest_by": "pub_date",
            },
            bases=(models.Model,),
        ),
    ]
