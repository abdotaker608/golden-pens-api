# Generated by Django 3.0.7 on 2021-01-05 16:05

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0008_auto_20210105_1804'),
    ]

    operations = [
        migrations.AlterField(
            model_name='story',
            name='tags',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=100), blank=True, default=list, size=30),
        ),
    ]