# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-05 20:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("coltrane", "0002_auto_20170528_0928"),
    ]

    operations = [
        migrations.AlterField(
            model_name="post",
            name="enable_comments",
            field=models.BooleanField(default=False),
        ),
    ]
