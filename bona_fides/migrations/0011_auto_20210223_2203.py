# Generated by Django 3.1.7 on 2021-02-23 22:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("bona_fides", "0010_auto_20210220_1641"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="award",
            options={},
        ),
        migrations.AlterModelOptions(
            name="skill",
            options={},
        ),
        migrations.AlterModelOptions(
            name="socialmediaprofile",
            options={},
        ),
        migrations.RemoveField(
            model_name="award",
            name="order",
        ),
        migrations.RemoveField(
            model_name="skill",
            name="order",
        ),
        migrations.RemoveField(
            model_name="socialmediaprofile",
            name="order",
        ),
    ]
