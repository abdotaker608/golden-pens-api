# Generated by Django 3.0.7 on 2021-01-21 14:50

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0011_auto_20210117_1632'),
    ]

    operations = [
        migrations.AlterField(
            model_name='story',
            name='tags',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=1500), default=list, size=30),
        ),
    ]
