# Generated by Django 3.0.7 on 2021-01-13 11:51

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0009_auto_20210105_1805'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chapter',
            name='views',
        ),
        migrations.AddField(
            model_name='chapter',
            name='views',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=500), default=list, size=None),
        ),
        migrations.AlterField(
            model_name='story',
            name='tags',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=100), default=list, size=30),
        ),
    ]
