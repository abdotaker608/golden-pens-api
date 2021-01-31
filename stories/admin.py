from django.contrib import admin
from .models import Story, Report, Chapter


class ReportAdmin(admin.ModelAdmin):

    list_display = ['pk', 'get_user', 'get_story', 'original']
    search_fields = ['pk', 'story__title']
    model = Report

    def get_user(self, obj):
        return obj.user.pk

    get_user.short_description = 'User'

    def get_story(self, obj):
        return obj.story.pk

    get_story.short_description = 'Story'


class StoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'pk', 'get_author', 'get_views', 'get_loves']
    search_fields = ['pk', 'author__nickname', 'author__user__first_name', 'author__user__last_name']

    def get_author(self, obj):
        return obj.author.nickname is not None and obj.author.nickname or obj.author.user.fullname()

    get_author.short_description = 'Author'

    def get_loves(self, obj):
        return obj.get_stats()['loves']

    get_loves.short_description = 'Loves'

    def get_views(self, obj):
        return obj.get_stats()['views']

    get_views.short_description = 'Views'


class ChapterAdmin(admin.ModelAdmin):
    list_display = ['title', 'pk', 'get_story']
    search_fields = ['title', 'pk', 'story__title', 'story__author__nickname', 'story__author__user__first_name',
                     'story__author__user__last_name']

    def get_story(self, obj):
        return obj.story.title

    get_story.short_description = 'Story'


admin.site.register(Report, ReportAdmin)
admin.site.register(Chapter, ChapterAdmin)
admin.site.register(Story, StoryAdmin)
