# Generated by Django 3.0.7 on 2021-01-04 19:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0004_story_arr'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='story',
            name='arr',
        ),
    ]