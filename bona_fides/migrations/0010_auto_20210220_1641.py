# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2021-02-20 16:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bona_fides', '0009_auto_20170909_1132'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clip',
            name='type',
            field=models.CharField(choices=[('app', 'App'), ('lesson-plan', 'Lesson plan'), ('story', 'Story'), ('software', 'Software')], max_length=100),
        ),
        migrations.AlterField(
            model_name='talk',
            name='date',
            field=models.DateField(help_text='The date of the talk'),
        ),
        migrations.AlterField(
            model_name='talk',
            name='location',
            field=models.CharField(help_text='The location of the venue', max_length=1000),
        ),
        migrations.AlterField(
            model_name='talk',
            name='title',
            field=models.CharField(help_text='The title of the talk', max_length=1000),
        ),
        migrations.AlterField(
            model_name='talk',
            name='venue',
            field=models.CharField(help_text='The host of the talk', max_length=1000),
        ),
    ]
