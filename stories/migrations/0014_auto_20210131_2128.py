# Generated by Django 3.0.7 on 2021-01-31 19:28

import django.contrib.postgres.indexes
from django.db import migrations
from django.contrib.postgres.operations import BtreeGinExtension


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0013_auto_20210126_1938'),
    ]

    operations = [
        BtreeGinExtension(),
        migrations.AddIndex(
            model_name='story',
            index=django.contrib.postgres.indexes.GinIndex(fields=['title', 'category', 'tags'], name='stories_sto_title_5ec1d5_gin'),
        ),
    ]