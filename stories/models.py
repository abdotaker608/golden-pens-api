from django.db import models
from .defaults import story_categories
from authentication.models import Author, User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.fields import ArrayField
from .managers import StoryManager
import os
from django.contrib.postgres.indexes import GinIndex


def get_path(instance, filename, *args):
    path = 'Story Covers'
    name = f'{instance.id}_story_cover.{filename.split(".")[1]}'
    return os.path.join(path, name)


class Story(models.Model):
    author = models.ForeignKey(Author, related_name='stories', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(default='')
    tags = ArrayField(models.CharField(max_length=1500, blank=True), size=30, default=list)
    category = models.CharField(max_length=500, choices=story_categories)
    cover = models.ImageField(upload_to=get_path)
    finished = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.id is None:
            image = self.cover
            self.cover = None
            super(Story, self).save(*args, **kwargs)
            self.cover = image
            if 'force_insert' in kwargs:
                kwargs.pop('force_insert')
        super(Story, self).save(*args, **kwargs)

    # Managers
    objects = models.Manager()
    advanced = StoryManager()

    class Meta:
        verbose_name_plural = 'stories'
        indexes = [GinIndex(fields=['title', 'category', 'tags'])]

    def __str__(self):
        return self.title

    def get_stats(self):
        stats = {
            'views': 0,
            'loves': 0,
            'replies': 0
        }

        for chapter in self.chapters.all():
            stats['views'] += len(chapter.views)
            stats['loves'] += chapter.loves.count()
            stats['replies'] += chapter.replies.count()

        return stats


class Chapter(models.Model):
    story = models.ForeignKey(Story, related_name='chapters', on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    content = models.TextField()
    number = models.IntegerField(null=True)
    loves = models.ManyToManyField(User, related_name='loves', blank=True)
    views = ArrayField(models.CharField(max_length=500, blank=True), default=list)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def next(self):
        chapter = self.story.chapters.filter(number=self.number+1)
        if chapter.exists():
            return chapter[0].pk

    def prev(self):
        if self.number != 1:
            return self.story.chapters.get(number=self.number-1).pk


@receiver(post_save, sender=Chapter)
def number_the_chapter(sender, instance, created, **kwargs):
    if created:
        chapters = instance.story.chapters.exclude(pk=instance.pk)
        if chapters.count() == 0:
            instance.number = 1
        else:
            instance.number = chapters.last().number + 1
        instance.save()


class Reply(models.Model):
    user = models.ForeignKey(User, related_name='replies', on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, related_name='replies', on_delete=models.CASCADE)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)


class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='reports')
    original = models.CharField(max_length=500)
    comment = models.TextField(null=True)

    def __str__(self):
        return str(self.pk)
