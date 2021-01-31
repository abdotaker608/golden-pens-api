from authentication.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Story, Chapter


classic_register_data = {
    'first_name': 'John',
    'last_name': 'Smith',
    'email': 'John@example.com',
    'password': '1234',
}


def get_auth_user(email='John@example.com'):
    classic_register_data['email'] = email
    user = User.objects.create_user(**classic_register_data)
    return user


def create_test_story(email='John@example.com'):
    user = get_auth_user(email)
    with open('stories/testImage.png', 'rb') as image:
        cover = SimpleUploadedFile('cover.png', image.read(), 'image/png')
    story = Story.objects.create(
        title='Title',
        author=user.author,
        cover=cover,
        category='quest'
    )
    return story


def create_adv_test_story(data, email='John@example.com'):
    user = get_auth_user(email)
    with open('stories/testImage.png', 'rb') as image:
        cover = SimpleUploadedFile('cover.png', image.read(), 'image/png')
    story = Story.objects.create(
        author=user.author,
        cover=cover,
        **data
    )
    return story


def create_test_chapter(story):
    chapter = Chapter.objects.create(
        story=story,
        title='Chapter',
        content='Chapter Content'
    )
    return chapter
