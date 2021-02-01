from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
from .signals import initialize_user
import jwt
from django.conf import settings
from datetime import datetime, timedelta
import pytz
from django.utils import timezone
from django.contrib.postgres.fields import JSONField


class User(AbstractBaseUser, PermissionsMixin):

    social_id = models.CharField(max_length=500, null=True, blank=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    picture = models.ImageField(upload_to='Profiles', null=True, blank=True)
    social_picture = models.CharField(max_length=500, null=True, blank=True)
    cover = models.ImageField(upload_to='Covers', null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    email_verified = models.BooleanField(default=False)
    temp_email = models.EmailField(null=True, blank=True)
    joined = models.DateField(auto_now_add=True, editable=False)
    last_password_reset = models.DateTimeField(null=True, blank=True)
    current_reset_token = models.CharField(max_length=500, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.fullname()

    def fullname(self):
        return f'{self.first_name} {self.last_name}'

    def get_jwt(self):
        return jwt.encode({'pk': self.pk, 'exp': datetime.now() + timedelta(days=30)},
                          settings.SECRET_KEY, algorithm='HS256').decode()

    def get_auth_jwt(self):
        return jwt.encode({'email': self.email, 'exp': datetime.now() + timedelta(days=3)},
                          settings.SECRET_KEY, algorithm='HS256').decode()

    def with_provider(self):
        return self.social_id is not None

    def token(self):
        return self.auth_token.key

    def reset_request_allowed(self):
        if self.last_password_reset is not None:
            day_passed = (self.last_password_reset + timedelta(days=1)) <= pytz.UTC.localize(datetime.now())
            if day_passed:
                self.last_password_reset = timezone.now()
                self.save()
            return day_passed
        self.last_password_reset = timezone.now()
        self.save()
        return True


@receiver(post_save, sender=User)
def init_callback(sender, instance, created, **kwargs):
    if created:
        initialize_user(instance)


def get_default_social():
    return {'fb': None, 'insta': None, 'twitter': None}


class Author(models.Model):
    user = models.OneToOneField(User, related_name='author', primary_key=True, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=50, null=True, blank=True)
    followers = models.ManyToManyField(User, related_name='followers', blank=True)
    social = JSONField(default=get_default_social)

    def __str__(self):
        return self.user.email

    def stories_no(self):
        return self.stories.count()

    def followers_count(self):
        return self.followers.count()
