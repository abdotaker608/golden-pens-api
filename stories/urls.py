from django.urls import path
from . import views

app_name = 'stories'

urlpatterns = [
    path('create', views.StoryCreationView.as_view(), name='story_create'),
    path('update/<int:pk>', views.StoryCreationView.as_view(), name='story_create'),
    path('overview/<int:pk>', views.story_overview, name='story_overview'),
    path('update_follow', views.update_follow, name='update_follow'),
    path('overview/chapters/<int:pk>', views.ChaptersOverview.as_view(), name='chapters_overview'),
    path('report', views.ReportView.as_view(), name='report_story'),
    path('create/chapter', views.ChapterCreationView.as_view(), name='chapter_create'),
    path('update/chapter/<int:pk>', views.ChapterCreationView.as_view(), name='chapter_update'),
    path('chapters/<int:pk>', views.chapter_view, name='chapter_view'),
    path('view/chapter/<int:pk>', views.update_chapter_views, name='update_chapter_view'),
    path('love/chapter/<int:pk>', views.update_chapter_love, name='update_chapter_love'),
    path('chapter/<int:pk>/replies', views.ReplyView.as_view(), name='reply_view'),
    path('replies/create', views.ReplyCreationView.as_view(), name='reply_create'),
    path('replies/update/<int:pk>', views.ReplyCreationView.as_view(), name='reply_update'),
    path('list', views.StoriesAdvancedView.as_view(), name='stories_advanced'),
    path('list/latest', views.LatestStories.as_view(), name='latest'),
    path('list/trending', views.TrendingStories.as_view(), name='trending'),
    path('list/<int:pk>', views.MyStories.as_view(), name='mine'),
    path('list/follow/<int:pk>', views.FollowingStories.as_view(), name='following'),
    path('save/<int:pk>', views.SaveFetchView.as_view(), name='save_fetch')
]