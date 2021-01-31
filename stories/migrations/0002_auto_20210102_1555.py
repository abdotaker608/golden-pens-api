# Generated by Django 3.0.7 on 2021-01-02 13:55

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stories', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='view',
            name='chapter',
        ),
        migrations.RemoveField(
            model_name='view',
            name='user',
        ),
        migrations.AddField(
            model_name='chapter',
            name='loves',
            field=models.ManyToManyField(related_name='loves', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='chapter',
            name='views',
            field=models.ManyToManyField(related_name='views', to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='Love',
        ),
        migrations.DeleteModel(
            name='View',
        ),
    ]