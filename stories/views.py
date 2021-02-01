from rest_framework import generics, mixins
from .serializers import StoryCreateSerializer, StorySerializer, ChapterOverviewSerializer, ReportSerializer, \
    ChapterCreateSerializer, ChapterSerializer, ReplySerializer, ReplyCreationSerializer, StoryAdvSerializer,\
    StorySaveSerializer
from .models import Story, Chapter, Report, Reply
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from authentication.models import User
from rest_framework.response import Response
from rest_framework import status
from authentication.utils import validate_auth
from .pagination import RepliesPaginator, StoriesPaginator
import socket


class StoryCreationView(generics.GenericAPIView, mixins.CreateModelMixin, mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin, mixins.RetrieveModelMixin):
    serializer_class = StoryCreateSerializer
    queryset = Story.objects.all()

    def post(self, request):
        if not validate_auth(request, request.data['author'], 'user'):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return self.create(request)

    def put(self, request, pk):
        if not validate_auth(request, pk, 'story'):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return self.update(request, pk, partial=True)

    def delete(self, request, pk):
        if not validate_auth(request, pk, 'story'):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return self.destroy(request, pk)

    def get(self, request, pk):
        return self.retrieve(request, pk)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def story_overview(request, pk):
    user_pk = request.GET.get('user')
    story = Story.objects.get(id=pk)
    serializer = StorySerializer(story)
    if user_pk is not None:
        serializer.data['author']['inFollowers'] = story.author.followers.filter(pk=user_pk).exists()
    return Response(serializer.data, status=status.HTTP_200_OK)


class ChaptersOverview(generics.GenericAPIView, mixins.ListModelMixin):
    serializer_class = ChapterOverviewSerializer
    queryset = None
    authentication_classes = []
    permission_classes = []

    def get(self, request, pk):
        self.queryset = Chapter.objects.filter(story__id=pk)
        return self.list(request)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def chapter_view(request, pk):
    user_pk = request.GET.get('user')
    chapter = Chapter.objects.get(id=pk)
    serializer = ChapterSerializer(chapter)
    data = serializer.data
    if user_pk is not None:
        data['loved'] = chapter.loves.filter(pk=user_pk).exists()
        data['story']['author']['inFollowers'] = chapter.story.author.followers.filter(pk=user_pk).exists()
    return Response(data, status=status.HTTP_200_OK)


class ChapterCreationView(generics.GenericAPIView, mixins.CreateModelMixin, mixins.UpdateModelMixin,
                          mixins.DestroyModelMixin):
    queryset = Chapter.objects.all()
    serializer_class = ChapterCreateSerializer

    def post(self, request):
        if not validate_auth(request, request.data['story'], 'story'):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return self.create(request)

    def put(self, request, pk):
        if not validate_auth(request, pk, 'chapter'):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return self.update(request, pk, partial=True)

    def delete(self, request, pk):
        if not validate_auth(request, pk, 'chapter'):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return self.destroy(request, pk)


@api_view(['POST'])
def update_follow(request):
    user_pk = request.data['user']
    author_pk = request.data['author']

    if user_pk == author_pk:
        return Response({'success': False}, status=status.HTTP_200_OK)

    if not validate_auth(request, user_pk, 'user'):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    author = User.objects.get(pk=author_pk)
    user = User.objects.get(pk=user_pk)

    if author.author.followers.filter(pk=user_pk).exists():
        author.author.followers.remove(user)
    else:
        author.author.followers.add(user)

    return Response({'success': True}, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def update_chapter_views(request, pk):
    chapter = Chapter.objects.get(pk=pk)
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')

    if ip_address not in chapter.views:
        try:
            socket.inet_aton(ip_address)
            chapter.views.append(ip_address)
            chapter.save()
        except socket.error:
            pass
    return Response({'success': True}, status=status.HTTP_200_OK)


@api_view(['POST'])
def update_chapter_love(request, pk):
    user_pk = request.data['user']

    if not validate_auth(request, user_pk, 'user'):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    chapter = Chapter.objects.get(pk=pk)

    user = User.objects.get(pk=user_pk)

    if chapter.loves.filter(pk=user_pk).exists():
        chapter.loves.remove(user)
    else:
        chapter.loves.add(user)

    return Response({'success': True}, status=status.HTTP_200_OK)


class ReportView(generics.GenericAPIView, mixins.CreateModelMixin):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    def post(self, request):
        if not validate_auth(request, request.data['user'], 'user'):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return self.create(request)


class ReplyView(generics.GenericAPIView, mixins.ListModelMixin):
    queryset = None
    serializer_class = ReplySerializer
    pagination_class = RepliesPaginator
    authentication_classes = []
    permission_classes = []

    def get(self, request, pk):
        self.queryset = Reply.objects.filter(chapter__pk=pk).order_by('-created')
        return self.list(request)


class ReplyCreationView(generics.GenericAPIView, mixins.CreateModelMixin, mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin):
    queryset = Reply.objects.all()
    serializer_class = ReplyCreationSerializer

    def post(self, request):
        if not validate_auth(request, request.data['user'], 'user'):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return self.create(request)

    def put(self, request, pk):
        if not validate_auth(request, pk, 'reply'):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return self.update(request, pk, partial=True)

    def delete(self, request, pk):
        if not validate_auth(request, pk, 'reply'):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return self.destroy(request, pk)


class StoriesAdvancedView(generics.GenericAPIView, mixins.ListModelMixin):
    queryset = None
    serializer_class = StoryAdvSerializer
    pagination_class = StoriesPaginator
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        search = request.GET.get('search')
        cat = request.GET.get('cat')
        sub_cat = request.GET.get('subCat')
        sub_cat_ar = request.GET.get('subCatAr')
        sort = request.GET.get('sort') or '-created'
        follower_pk = request.GET.get('onF')
        author_id = request.GET.get('author')
        self.queryset = Story.advanced.find(search=search, cat=cat, sub_cat=sub_cat, sub_cat_ar=sub_cat_ar,
                                              sort=sort, follower_pk=follower_pk, author_id=author_id)
        return self.list(request)


class LatestStories(generics.GenericAPIView, mixins.ListModelMixin):
    serializer_class = StoryAdvSerializer
    queryset = Story.advanced.latest(limit=10)
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return self.list(request)


class TrendingStories(generics.GenericAPIView, mixins.ListModelMixin):
    serializer_class = StoryAdvSerializer
    queryset = Story.advanced.trending(limit=10)
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return self.list(request)


class MyStories(generics.GenericAPIView, mixins.ListModelMixin):
    serializer_class = StoryAdvSerializer
    queryset = None
    authentication_classes = []
    permission_classes = []

    def get(self, request, pk):
        self.queryset = Story.advanced.personal(pk, limit=10)
        return self.list(request)


class FollowingStories(generics.GenericAPIView, mixins.ListModelMixin):
    serializer_class = StoryAdvSerializer
    queryset = None
    authentication_classes = []
    permission_classes = []

    def get(self, request, pk):
        self.queryset = Story.advanced.following(pk, limit=10)
        if not self.queryset.exists():
            return Response({"message": "noFollow"}, status=status.HTTP_204_NO_CONTENT)
        return self.list(request)


class SaveFetchView(generics.GenericAPIView, mixins.RetrieveModelMixin):

    serializer_class = StorySaveSerializer
    authentication_classes = []
    permission_classes = []
    queryset = Story.objects.all()

    def get(self, request, pk):
        return self.retrieve(request, pk)