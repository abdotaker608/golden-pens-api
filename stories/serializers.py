from rest_framework.serializers import ModelSerializer, ReadOnlyField
from .models import Story, Chapter, Report, Reply
from authentication.models import User, Author


class UserSerializer(ModelSerializer):

    fullname = ReadOnlyField()

    class Meta:
        fields = ['pk', 'fullname', 'picture', 'social_picture']
        model = User


class AuthorSimpleSerializer(ModelSerializer):

    user = UserSerializer()

    class Meta:
        fields = ['nickname', 'user']
        model = Author


class StoryAdvSerializer(ModelSerializer):

    author = AuthorSimpleSerializer()

    class Meta:
        fields = ['id', 'cover', 'title', 'created', 'author']
        model = Story


class ReplySerializer(ModelSerializer):

    user = UserSerializer()

    class Meta:
        fields = '__all__'
        model = Reply


class ReplyCreationSerializer(ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Reply


class AuthorSerializer(ModelSerializer):

    user = UserSerializer()

    class Meta:
        fields = '__all__'
        model = Author


class StorySerializer(ModelSerializer):

    author = AuthorSerializer()
    get_stats = ReadOnlyField()

    class Meta:
        fields = '__all__'
        model = Story


class StoryCreateSerializer(ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Story

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        tags = tags[0].split(',')
        Story.objects.filter(pk=instance.pk).update(**validated_data, tags=tags)
        return instance

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        tags = tags[0].split(',')
        story = Story.objects.create(**validated_data, tags=tags)
        return story


class ChapterCreateSerializer(ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Chapter


class ChapterSerializer(ModelSerializer):

    story = StorySerializer()
    next = ReadOnlyField()
    prev = ReadOnlyField()

    class Meta:
        fields = '__all__'
        model = Chapter


class ChapterOverviewSerializer(ModelSerializer):
    class Meta:
        fields = ['pk', 'title']
        model = Chapter


class ReportSerializer(ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Report


class StorySaveSerializer(ModelSerializer):

    class Meta:
        fields = ['chapters']
        model = Story
