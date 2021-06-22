from rest_framework.test import APITestCase
from django.shortcuts import reverse
from .models import Story, Report, Chapter, Reply
from .utils import get_auth_user, create_test_story, create_test_chapter, create_adv_test_story
from authentication.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
import datetime


class StoryTest(APITestCase):

    def test_creates_story(self):
        user = get_auth_user()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.token()}')
        with open('stories/testImage.png', 'rb') as image:
            cover = SimpleUploadedFile('cover.png', image.read(), 'image/png')
        story_data = {
            'title': 'Title',
            'category': 'quest',
            'cover': cover,
            'author': user.pk,
            'tags': ['']
        }
        response = self.client.post(reverse('stories:story_create'), story_data)
        stories = Story.objects.all()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(stories.count(), 1)
        story = stories[0]
        self.assertTrue(story.title, 'Title')
        self.assertTrue(story.category, 'quest')

    def test_retrieves_story_overview(self):
        story = create_test_story()
        response = self.client.get(reverse('stories:story_overview', args=[story.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], story.pk)

    def test_updates_story(self):
        story = create_test_story()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {story.author.user.token()}')
        self.assertEqual(story.title, 'Title')
        self.assertEqual(story.category, 'quest')
        self.assertEqual(story.tags, [])
        data = {
            'title': 'New Title',
            'category': 'overcome',
            'tags': ['tag1,tag2']
        }
        response = self.client.put(reverse('stories:story_create', args=[story.pk]), data, format='json')
        story = Story.objects.get(pk=story.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(story.title, data['title'])
        self.assertEqual(story.category, data['category'])
        self.assertEqual(story.tags, ['tag1', 'tag2'])

    def test_deletes_story(self):
        story = create_test_story()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {story.author.user.token()}')
        response = self.client.delete(reverse('stories:story_create', args=[story.pk]))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Story.objects.count(), 0)

    def test_creates_report(self):
        story = create_test_story()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {story.author.user.token()}')
        data = {
            'story': story.pk,
            'user': story.author.user.pk,
            'original': 'https://somesecurelink/'
        }
        response = self.client.post(reverse('stories:report_story'), data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Report.objects.count(), 1)

    def test_retrieves_stories(self):
        create_adv_test_story({'title': 'Story1', 'category': 'quest'})
        create_adv_test_story({'title': 'Story2', 'category': 'quest'}, email='Ex@ex.com')
        response = self.client.get(reverse('stories:stories_advanced'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)

    def test_retrieves_latest_stories(self):
        create_adv_test_story({'title': 'Story1', 'category': 'quest'})
        latest_story = create_adv_test_story({'title': 'Story2', 'category': 'quest'}, email='Ex@ex.com')
        url = f"{reverse('stories:stories_advanced')}?sort=-created"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['title'], latest_story.title)

    def test_retrieves_trending_stories(self):
        create_adv_test_story({'title': 'Story1', 'category': 'quest'})
        trend_story = create_adv_test_story({'title': 'Story2', 'category': 'quest'}, email='Ex@ex.com')
        chapter = create_test_chapter(trend_story)
        chapter.views.append('127.0.0.1')
        chapter.save()
        url = f"{reverse('stories:stories_advanced')}?sort=trending"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['title'], trend_story.title)

    def test_filters_categories_correctly(self):
        story1 = create_adv_test_story({'title': 'Story1', 'category': 'rebirth'})
        url = f"{reverse('stories:stories_advanced')}?cat=rebirth"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], story1.title)

    def test_filters_with_title_trigram_correctly(self):
        story1 = create_adv_test_story({'title': 'Romeo and Juliet', 'category': 'rebirth'})
        url = f"{reverse('stories:stories_advanced')}?search=Romeo"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], story1.title)

    def test_filters_with_tags_trigram_correctly(self):
        story1 = create_adv_test_story({'title': 'Bueaty and The Beast', 'category': 'rebirth', 'tags': ['Romance']})
        url = f"{reverse('stories:stories_advanced')}?search=Romantic"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], story1.title)

    def test_filters_with_fullname_trigram_correctly(self):
        story = create_adv_test_story({'title': 'Story1', 'category': 'quest'})
        url = f"{reverse('stories:stories_advanced')}?search=John"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], story.title)

    def test_filters_with_nickname_trigram_correctly(self):
        story = create_adv_test_story({'title': 'Story1', 'category': 'quest'})
        story.author.nickname = 'Mr. Wolfie'
        story.author.save()
        url = f"{reverse('stories:stories_advanced')}?search=wolfie"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], story.title)

    def test_filters_with_category_trigram_correctly(self):
        story = create_adv_test_story({'title': 'Story1', 'category': 'overcome'})
        url = f"{reverse('stories:stories_advanced')}?search=overcoming"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], story.title)

    def test_filters_only_following_correctly(self):
        create_test_story()
        story = create_test_story(email='ex@ex.com')
        user = get_auth_user(email='my@email.com')
        story.author.followers.add(user)
        url = f"{reverse('stories:stories_advanced')}?onF={user.pk}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], story.id)

    def test_fetches_trending_stories(self):
        create_test_story()
        story = create_test_story(email='ex@ex.com')
        chapter = create_test_chapter(story)
        chapter.views.append('127.0.0.1')
        chapter.save()
        response = self.client.get(reverse('stories:trending'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['title'], story.title)

    def test_fetches_trending_latest_stories(self):
        story1 = create_test_story()
        story = create_test_story(email='ex@ex.com')
        story.created = timezone.now() - datetime.timedelta(days=8)
        chapter = create_test_chapter(story)
        chapter.views.append('127.0.0.1')
        chapter.save()
        story.save()
        response = self.client.get(reverse('stories:trending'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], story1.title)

    def test_fetches_latest_stories(self):
        create_test_story()
        story = create_test_story(email='ex@ex.com')
        response = self.client.get(reverse('stories:latest'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['title'], story.title)

    def test_fetches_user_story(self):
        create_test_story()
        story = create_test_story(email='my@email.com')
        response = self.client.get(reverse('stories:mine', args=[story.author.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        story = Story.objects.get(pk=response.data[0]['id'])
        self.assertEqual(story.author.user.email, 'my@email.com')

    def test_fetches_following_stories(self):
        create_test_story()
        story = create_test_story(email='ex@ex.com')
        user = get_auth_user(email='my@email.com')
        story.author.followers.add(user)
        response = self.client.get(reverse('stories:following', args=[user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], story.id)

    def test_fetches_data_for_saving_story(self):
        story = create_test_story()
        create_test_chapter(story)
        create_test_chapter(story)
        response = self.client.get(reverse('stories:save_fetch', args=[story.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['chapters']), 2)


class ChapterTest(APITestCase):

    def test_retrieves_chapters(self):
        story = create_test_story()
        create_test_chapter(story)
        create_test_chapter(story)
        response = self.client.get(reverse('stories:chapters_overview', args=[story.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_creates_chapter(self):
        story = create_test_story()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {story.author.user.token()}')
        data = {
            'title': 'Ch1',
            'story': story.pk,
            'content': 'Test Chapter'
        }
        response = self.client.post(reverse('stories:chapter_create'), data, format='json')
        chapters = Chapter.objects.all()
        chapter = chapters[0]
        self.assertEqual(response.status_code, 201)
        self.assertEqual(chapters.count(), 1)
        self.assertEqual(chapter.title, data['title'])

    def test_increments_number_of_chapter(self):
        story = create_test_story()
        chapter = create_test_chapter(story)
        self.assertEqual(chapter.number, 1)
        chapter2 = create_test_chapter(story)
        self.assertEqual(chapter2.number, 2)
        chapter3 = create_test_chapter(story)
        self.assertEqual(chapter3.number, 3)
        chapter4 = create_test_chapter(story)
        self.assertEqual(chapter4.number, 4)
        story2 = create_test_story('ex@example.com')
        chapter5 = create_test_chapter(story2)
        self.assertEqual(chapter5.number, 1)

    def test_retrieves_chapter(self):
        story = create_test_story()
        chapter = create_test_chapter(story)
        response = self.client.get(reverse('stories:chapter_view', args=[chapter.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], chapter.title)

    def test_saves_chapter(self):
        story = create_test_story()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {story.author.user.token()}')
        chapter = create_test_chapter(story)
        data = {'title': 'Updated Title', 'content': 'Updated Content'}
        response = self.client.put(reverse('stories:chapter_update', args=[chapter.pk]), data, format='json')
        chapter = Chapter.objects.get(pk=chapter.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(chapter.title, data['title'])
        self.assertEqual(chapter.content, data['content'])

    def test_adds_view(self):
        story = create_test_story()
        chapter = create_test_chapter(story)
        self.assertEqual(len(chapter.views), 0)
        response = self.client.get(reverse('stories:update_chapter_view', args=[chapter.pk]))
        chapter = Chapter.objects.get(pk=chapter.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(chapter.views), 1)

    def test_adds_love(self):
        story = create_test_story()
        chapter = create_test_chapter(story)
        user = story.author.user
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.token()}')
        self.assertEqual(chapter.loves.count(), 0)
        data = {'user': user.pk}
        response = self.client.post(reverse('stories:update_chapter_love', args=[chapter.pk]), data, format='json')
        chapter = Chapter.objects.get(pk=chapter.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(chapter.loves.count(), 1)
        self.assertTrue(chapter.loves.filter(pk=user.pk).exists())

    def test_removes_love(self):
        story = create_test_story()
        chapter = create_test_chapter(story)
        user = story.author.user
        chapter.loves.add(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.token()}')
        data = {'user': user.pk}
        response = self.client.post(reverse('stories:update_chapter_love', args=[chapter.pk]), data, format='json')
        chapter = Chapter.objects.get(pk=chapter.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(chapter.loves.count(), 0)
        self.assertFalse(chapter.loves.filter(pk=user.pk).exists())


class AuthorTest(APITestCase):

    def test_adds_follow(self):
        author = User.objects.create_user(email='example@ex.com', password='1234')
        user = get_auth_user()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.token()}')
        self.assertEqual(author.author.followers.count(), 0)
        data = {
            'inFollowers': False,
            'user': user.pk,
            'author': author.pk
        }
        response = self.client.post(reverse('stories:update_follow'), data, format='json')
        author = User.objects.get(pk=author.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(author.author.followers.count(), 1)
        self.assertEqual(author.author.followers.first().pk, user.pk)

    def test_removes_follow(self):
        author = User.objects.create_user(email='example@ex.com', password='1234')
        user = get_auth_user()
        author.author.followers.add(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.token()}')
        self.assertEqual(author.author.followers.count(), 1)
        self.assertEqual(author.author.followers.first().pk, user.pk)
        data = {
            'inFollowers': True,
            'user': user.pk,
            'author': author.pk
        }
        response = self.client.post(reverse('stories:update_follow'), data, format='json')
        author = User.objects.get(pk=author.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(author.author.followers.count(), 0)


class ReplyTest(APITestCase):

    def test_fetch_replies(self):
        story = create_test_story()
        chapter = create_test_chapter(story)
        chapter.replies.create(user=story.author.user, content='New Reply')
        response = self.client.get(reverse('stories:reply_view', args=[chapter.pk]))
        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['content'], 'New Reply')

    def test_creates_reply(self):
        story = create_test_story()
        chapter = create_test_chapter(story)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {story.author.user.token()}')
        self.assertEqual(chapter.replies.count(), 0)
        data = {
            'user': story.author.user.pk,
            'chapter': chapter.pk,
            'content': 'Reply'
        }
        response = self.client.post(reverse('stories:reply_create'), data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(chapter.replies.count(), 1)
        self.assertEqual(chapter.replies.first().content, 'Reply')

    def test_updates_reply(self):
        story = create_test_story()
        chapter = create_test_chapter(story)
        reply = chapter.replies.create(user=story.author.user, content='Reply')
        data = {'content': 'Edit Reply'}
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {story.author.user.token()}')
        response = self.client.put(reverse('stories:reply_update', args=[reply.pk]), data, format='json')
        reply = Reply.objects.get(pk=reply.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(reply.content, data['content'])

    def test_deletes_reply(self):
        story = create_test_story()
        chapter = create_test_chapter(story)
        reply = chapter.replies.create(user=story.author.user, content='Reply')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {story.author.user.token()}')
        response = self.client.delete(reverse('stories:reply_update', args=[reply.pk]))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Reply.objects.count(), 0)

