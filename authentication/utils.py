from .models import User
from django.core.exceptions import ObjectDoesNotExist
import jwt
from django.conf import settings
from stories.models import Chapter, Story, Reply


def authenticate(email, password):
    try:
        user = User.objects.get(email=email)
        is_authenticated = user.check_password(password)
        if is_authenticated:
            return user
        return None
    except ObjectDoesNotExist:
        return None


def generate_test_token(payload):
    return jwt.encode({**payload, 'exp': 1}, settings.SECRET_KEY, algorithm='HS256').decode()


def validate_auth(request, pk, comp):
    def get_story_user():
        return Story.objects.get(pk=pk).author.user.token()

    def get_chapter_user():
        return Chapter.objects.get(pk=pk).story.author.user.token()

    def get_user():
        return User.objects.get(pk=pk).token()

    def get_reply_user():
        return Reply.objects.get(pk=pk).user.token()

    pk_factory = {
        'story': get_story_user,
        'chapter': get_chapter_user,
        'user': get_user,
        'reply': get_reply_user
    }
    auth = request.headers['Authorization']
    token = auth.split(' ')[1]
    try:
        return token == pk_factory[comp]()
    except ObjectDoesNotExist:
        return False


class NotVerifiedError(Exception):
    pass


class UsedToken(Exception):
    pass

