# Generated by Django 3.0.7 on 2021-01-26 17:38

from django.db import migrations, models
import stories.models


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0012_auto_20210121_1650'),
    ]

    operations = [
        migrations.AlterField(
            model_name='story',
            name='cover',
            field=models.ImageField(upload_to=stories.models.get_path),
        ),
    ]