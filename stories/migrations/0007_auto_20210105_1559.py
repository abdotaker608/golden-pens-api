# Generated by Django 3.0.7 on 2021-01-05 13:59

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0006_auto_20210105_1558'),
    ]

    operations = [
        migrations.AlterField(
            model_name='story',
            name='tags',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=700), default=list, size=30),
        ),
    ]