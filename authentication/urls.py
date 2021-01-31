from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('register', views.register_new_user, name='register_new_user'),
    path('auth_jwt', views.authenticate_jwt, name='authenticate_jwt'),
    path('login', views.login_user, name='login_user'),
    path('verify_email', views.verify_email, name='verify_email'),
    path('request_reset', views.send_reset_request, name='send_reset_request'),
    path('complete_reset', views.complete_reset, name='complete_reset'),
    path('update_user/<int:pk>', views.update_user, name='update_user'),
    path('update_author/<int:pk>', views.update_author, name='update_author'),
    path('update_security/<int:pk>', views.update_security, name='update_security'),
    path('authors', views.AuthorsListView.as_view(), name='authors'),
    path('profile/<int:pk>', views.UserProfileView.as_view(), name='profile'),
    path('profile/media', views.update_media, name='update_media'),
    path('delete/<int:pk>', views.delete_user, name='delete')
]