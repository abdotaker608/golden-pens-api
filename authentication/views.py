from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response
from rest_framework import status, generics, mixins
from django.core.mail import send_mail
from .models import User, Author
from .serializers import UserSerializer
from django.template.loader import render_to_string
from django.conf import settings
from django.db.transaction import atomic
import jwt
from .utils import authenticate, NotVerifiedError, UsedToken, validate_auth
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from smtplib import SMTPException
from .serializers import AuthorSimpleSerializer, UserProfileSerializer
from django.db.models import Count, Value
from django.db.models.functions import Greatest, Concat
from .pagination import AuthorsPaginator
from django.contrib.postgres.search import TrigramSimilarity
import re


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def register_new_user(request):
    if User.objects.filter(email=request.data.get('email')).exists():
        return Response({"message": "emailExists"}, status=status.HTTP_400_BAD_REQUEST)

    with_provider = request.data.pop('withProvider')

    if with_provider:
        user = User.objects.create_user(**request.data)
        user.email_verified = True
        user.last_login = timezone.now()
        user.save()
        serializer = UserSerializer(user)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    with atomic():
        user = User.objects.create_user(**request.data)
        html_string = render_to_string('email_verify.html',
                                       {'link': f'{settings.CURRENT_FRONTEND_HOST}/verify/{user.get_auth_jwt()}'})
        send_mail(
            'GP-Email Verification',
            'Verify your email at Golden Pens',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_string,
            fail_silently=False
        )

        return Response({"success": True, "message": "userCreated"}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def authenticate_jwt(request):
    try:
        token = request.data['token']
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(pk=payload['pk'])
        if not user.is_active:
            return Response({'message': 'suspended', 'status': 403}, status=status.HTTP_403_FORBIDDEN)
        user.last_login = timezone.now()
        user.save()
        serializer = UserSerializer(user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    except (jwt.DecodeError, ObjectDoesNotExist, jwt.ExpiredSignatureError):
        return Response({"message": "invalidToken", "status": 401}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@throttle_classes([AnonRateThrottle])
def login_user(request):
    email = request.data['email']
    password = request.data.get('password')
    with_provider = request.data.get('withProvider')

    if with_provider is True:
        try:
            user = User.objects.get(email=email)
            if not user.with_provider():
                return Response({'message': 'invalidCredits', "status": 401}, status=status.HTTP_401_UNAUTHORIZED)
            user.last_login = timezone.now()
            user.save()
            serializer = UserSerializer(user)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            request.data.pop('withProvider')
            user = User.objects.create_user(**request.data)
            user.last_login = timezone.now()
            user.email_verified = True
            user.save()
            serializer = UserSerializer(user)
            return Response(data=serializer.data, status=status.HTTP_200_OK)

    user = authenticate(email, password)

    if user is None or user.social_id is not None:
        return Response({'message': 'invalidCredits', "status": 401}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.email_verified:
        return Response({'message': 'verifyRequired', 'status': 403}, status=status.HTTP_403_FORBIDDEN)

    if not user.is_active:
        return Response({'message': 'suspended', 'status': 403}, status=status.HTTP_403_FORBIDDEN)

    user.last_login = timezone.now()
    user.save()
    serializer = UserSerializer(user)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def verify_email(request):
    token = request.data['token']
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(email=payload['email'])
        if not user.is_active or user.email_verified:
            return Response({'message': 'invalidToken', 'status': 401}, status=status.HTTP_401_UNAUTHORIZED)
        user.email_verified = True
        user.last_login = timezone.now()
        user.save()
        serializer = UserSerializer(user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    except (ObjectDoesNotExist, jwt.DecodeError, jwt.ExpiredSignatureError):
        return Response({'message': 'invalidToken', 'status': 401}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def send_reset_request(request):
    email = request.data['email']
    try:
        user = User.objects.get(email=email)
        if user.with_provider():
            return Response({"message": "emailNotExist", "status": 400}, status=status.HTTP_400_BAD_REQUEST)
        if not user.email_verified:
            raise NotVerifiedError("Email is not verified")
        with atomic():
            if user.reset_request_allowed():
                token = user.get_auth_jwt()
                html_string = render_to_string('request_reset.html', {
                    'link': f'{settings.CURRENT_FRONTEND_HOST}/reset/{token}'
                })
                user.current_reset_token = token
                user.save()
                send_mail(
                    'Password Reset Request',
                    'You requested a password reset for your account',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                    html_message=html_string
                )
                return Response({"message": "recoverPasswordSent", "success": True}, status=status.HTTP_200_OK)
            return Response({"message": "waitResetAllow", "status": 429}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    except (ObjectDoesNotExist, NotVerifiedError, SMTPException):
        return Response({"message": "emailNotExist", "status": 400}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def complete_reset(request):
    token = request.data['token']
    new_password = request.data['password']

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(email=payload['email'])
        if user.current_reset_token != token:
            raise UsedToken("This token has already been used!")
        user.set_password(new_password)
        # Set the current reset token value to none so that the current jwt token is invalidated in future requests
        user.current_reset_token = None
        user.save()
        serializer = UserSerializer(user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    except (ObjectDoesNotExist, jwt.DecodeError, jwt.ExpiredSignatureError, UsedToken):
        return Response({"message": "invalidToken", "status": 401}, status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def update_user(request, pk):
    email = request.data['email']
    first_name = request.data['first_name']
    last_name = request.data['last_name']
    user = User.objects.get(pk=pk)

    if user.social_id is not None or not validate_auth(request, pk, 'user'):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    if user.email != email:
        if User.objects.filter(email=email).exists():
            return Response({"message": "emailExists", "status": 400}, status=status.HTTP_400_BAD_REQUEST)
        with atomic():
            html_string = render_to_string('new_email_verify.html',
                                           {'link': f'{settings.CURRENT_FRONTEND_HOST}/verifyC/{user.get_auth_jwt()}'})
            send_mail(
                'New Email Verification',
                'Verify your new email at GP',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=html_string,
                fail_silently=False
            )
            user.temp_email = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            return Response({"success": True, "message": "userCreated"}, status=status.HTTP_200_OK)
    else:
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        return Response({"success": True, "message": "saved"}, status=status.HTTP_200_OK)


@api_view(['POST'])
def update_author(request, pk):
    nickname = request.data['author']['nickname']
    social = request.data['author']['social']
    user = User.objects.get(pk=pk)

    if not validate_auth(request, pk, 'user'):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    if social['fb'] is not None:
        regex = r'^(https://)?(www.)?(facebook.com)\/((profile.php\?id=[\d]+)|([\w]+((\.|-)[\w]+)*))(/)?$'
        if re.match(regex, social['fb']) is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
    if social['insta'] is not None:
        regex = r'^(https://)?(www.)?(instagram.com)\/([\w]+(\.[\w]+)*)(/)?$'
        if re.match(regex, social['insta']) is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
    if social['twitter'] is not None:
        regex = r'^(https://)?(www.)?(twitter.com)\/[\w]+(/)?$'
        if re.match(regex, social['twitter']) is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    if user.author.nickname != nickname:
        if User.objects.filter(author__nickname=nickname).exists():
            return Response({"message": "nameExists"}, status=status.HTTP_400_BAD_REQUEST)
    user.author.nickname = nickname
    user.author.social = social
    user.author.save()
    return Response({"success": True, "message": "saved"}, status=status.HTTP_200_OK)


@api_view(['POST'])
def update_security(request, pk):
    current_password = request.data['currentPassword']
    new_password = request.data['password']
    user = User.objects.get(pk=pk)

    if user.social_id is not None or not validate_auth(request, pk, 'user'):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    if user.check_password(current_password):
        user.set_password(new_password)
        user.save()
        return Response({"success": True, "message": "saved"}, status=status.HTTP_200_OK)
    return Response({"message": "incorrectPassword", "status": 401}, status=status.HTTP_401_UNAUTHORIZED)


class AuthorsListView(generics.GenericAPIView, mixins.ListModelMixin):
    serializer_class = AuthorSimpleSerializer
    queryset = Author.objects.annotate(top=Count('followers'), stories_no=Count('stories')). \
        filter(stories_no__gte=1).order_by('-top')
    permission_classes = []
    authentication_classes = []
    pagination_class = AuthorsPaginator

    def get(self, request):
        search = request.GET.get('search')
        if search is not None:
            self.queryset = self.queryset.annotate(fullname=Concat('user__first_name', Value(' '), 'user__last_name'),
                                                   similarity=Greatest(
                                                       TrigramSimilarity('fullname', search),
                                                       TrigramSimilarity('nickname', search)
                                                   )).filter(similarity__gte=0.1).order_by('-similarity')
        return self.list(request)


class UserProfileView(generics.GenericAPIView, mixins.RetrieveModelMixin):

    serializer_class = UserProfileSerializer
    authentication_classes = []
    permission_classes = []
    queryset = User.objects.all()

    def get(self, request, pk):
        return self.retrieve(request, pk)


@api_view(['POST'])
def delete_user(request, pk):
    if not validate_auth(request, pk, 'user'):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    password = request.data['password']

    try:
        user = User.objects.get(pk=pk)
        if user.check_password(password):
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def update_media(request):
    user_pk = request.data['user']
    if not validate_auth(request, user_pk, 'user'):
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    picture = request.FILES.get('picture')
    cover = request.FILES.get('cover')
    user = User.objects.get(pk=user_pk)
    if picture is not None:
        user.picture = picture
    if cover is not None:
        user.cover = cover
    user.save()
    return Response({'success': True}, status=status.HTTP_200_OK)
