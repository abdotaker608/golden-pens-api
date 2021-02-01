from .models import User, Author
from rest_framework.serializers import ModelSerializer, ReadOnlyField


class AuthorSerializer(ModelSerializer):

    followers = ReadOnlyField(source='followers_count')

    class Meta:
        fields = '__all__'
        model = Author


class UserSerializer(ModelSerializer):

    get_jwt = ReadOnlyField()
    token = ReadOnlyField()
    with_provider = ReadOnlyField()
    author = AuthorSerializer(required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'picture', 'social_picture', 'cover', 'pk', 'get_jwt',
                  'token', 'with_provider', 'author']


class UserSimpleSerializer(ModelSerializer):

    fullname = ReadOnlyField()

    class Meta:
        fields = ['pk', 'social_picture', 'picture', 'fullname']
        model = User


class AuthorSimpleSerializer(ModelSerializer):

    user = UserSimpleSerializer()
    followers = ReadOnlyField(source='followers_count')

    class Meta:
        fields = ['user', 'nickname', 'followers']
        model = Author


class AuthorProfileSerializer(ModelSerializer):

    stories = ReadOnlyField(source='stories_no')
    followers = ReadOnlyField(source='followers_count')

    class Meta:
        fields = ['nickname', 'followers', 'stories', 'social']
        model = Author


class UserProfileSerializer(ModelSerializer):

    author = AuthorProfileSerializer()
    fullname = ReadOnlyField()

    class Meta:
        fields = ['pk', 'social_picture', 'picture', 'fullname', 'cover', 'author']
        model = User
