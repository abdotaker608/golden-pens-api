from rest_framework.test import APITestCase
from django.shortcuts import reverse
from django.core import mail
from .models import User
from .utils import generate_test_token
from datetime import datetime, timedelta
from django.utils import timezone
from stories.utils import create_test_story
from django.core.files.uploadedfile import SimpleUploadedFile

classic_register_data = {
    'first_name': 'John',
    'last_name': 'Smith',
    'email': 'John@example.com',
    'password': '1234',
}


class AuthSignup(APITestCase):

    def test_creates_social_user(self):
        register_data = {
            **classic_register_data,
            'social_id': '1234-1234',
            'social_picture': 'https://picture_url/',
            'withProvider': True,
            'password': None
        }
        response = self.client.post(reverse('authentication:register_new_user'), register_data, format='json')
        users = User.objects.all()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(users.count(), 1)
        user = users[0]
        self.assertEqual(user.email, 'John@example.com')
        self.assertTrue(user.email_verified)

    def test_creates_user(self):
        data = {**classic_register_data, 'withProvider': False}
        response = self.client.post(reverse('authentication:register_new_user'), data, format='json')
        users = User.objects.all()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(users.count(), 1)
        user = users[0]
        self.assertEqual(user.email, 'John@example.com')
        self.assertFalse(user.email_verified)
        self.assertEqual(len(mail.outbox), 1)

    def test_email_unique_constraint(self):
        data = {**classic_register_data, 'withProvider': False}
        User.objects.create_user(email='John@example.com', password='1234')
        response = self.client.post(reverse('authentication:register_new_user'), data, format='json')
        users = User.objects.all()
        self.assertEqual(users.count(), 1)
        self.assertEqual(response.status_code, 400)


class AuthVerification(APITestCase):
    def test_authenticate_valid_jwt(self):
        user = User.objects.create_user(**classic_register_data)
        response = self.client.post(reverse('authentication:authenticate_jwt'), {'token': user.get_jwt()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['pk'], user.pk)

    def test_authenticate_invalid_jwt(self):
        response = self.client.post(reverse('authentication:authenticate_jwt'), {'token': 'invalidToken'})
        self.assertEqual(response.status_code, 401)

    def test_authenticate_valid_jwt_with_deleted_user(self):
        user = User.objects.create_user(**classic_register_data)
        token = user.get_jwt()
        user.delete()
        response = self.client.post(reverse('authentication:authenticate_jwt'), {'token': token})
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(response.status_code, 401)

    def test_authenticate_valid_jwt_with_suspended_user(self):
        user = User.objects.create_user(**classic_register_data)
        token = user.get_jwt()
        user.is_active = False
        user.save()
        response = self.client.post(reverse('authentication:authenticate_jwt'), {'token': token})
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.status_code, 403)

    def test_verifies_email_with_valid_token(self):
        user = User.objects.create_user(**classic_register_data)
        token = user.get_auth_jwt()
        response = self.client.post(reverse('authentication:verify_email'), {'token': token}, format='json')
        user = User.objects.get(pk=user.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(user.email_verified)

    def test_denies_verify_email_with_invalid_token(self):
        user = User.objects.create_user(**classic_register_data)
        response = self.client.post(reverse('authentication:verify_email'), {'token': 'invalidToken'}, format='json')
        user = User.objects.get(pk=user.pk)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(user.email_verified)

    def test_denies_verifying_already_verified_email(self):
        user = User.objects.create_user(**classic_register_data)
        user.email_verified = True
        user.save()
        response = self.client.post(reverse('authentication:verify_email'),
                                    {'token': user.get_auth_jwt()}, format='json')
        user = User.objects.get(pk=user.pk)
        self.assertTrue(user.email_verified)
        self.assertEqual(response.status_code, 401)

    def test_denies_verifying_email_for_suspended_users(self):
        user = User.objects.create_user(**classic_register_data)
        user.is_active = False
        user.save()
        response = self.client.post(reverse('authentication:verify_email'),
                                    {'token': user.get_auth_jwt()}, format='json')
        user = User.objects.get(pk=user.pk)
        self.assertEqual(response.status_code, 401)

    def test_denies_verify_email_with_expired_token(self):
        user = User.objects.create_user(**classic_register_data)
        token = generate_test_token({'email': user.email})
        response = self.client.post(reverse('authentication:verify_email'), {'token': token}, format='json')
        user = User.objects.get(pk=user.pk)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(user.email_verified)

    def test_sends_reset_request_for_verified_email_with_day_passed_on_request_limit(self):
        user = User.objects.create_user(**classic_register_data)
        user.email_verified = True
        user.last_password_reset = datetime.now() - timedelta(days=1)
        user.save()
        response = self.client.post(reverse('authentication:send_reset_request'),
                                    {'email': user.email}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(mail.outbox), 1)

    def test_sends_reset_request_for_verified_email(self):
        user = User.objects.create_user(**classic_register_data)
        user.email_verified = True
        user.save()
        response = self.client.post(reverse('authentication:send_reset_request'),
                                    {'email': user.email}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(mail.outbox), 1)

    def test_rejects_sending_resets_for_unverified_emails(self):
        user = User.objects.create_user(**classic_register_data)
        response = self.client.post(reverse('authentication:send_reset_request'),
                                    {'email': user.email}, format='json')
        self.assertFalse(user.email_verified)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_rejects_sending_resets_for_social_users(self):
        register_data = {
            **classic_register_data,
            'social_id': '1234-1234',
            'social_picture': 'http://pic_url/'
        }
        user = User.objects.create_user(**register_data)
        response = self.client.post(reverse('authentication:send_reset_request'), {'email': user.email}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_rejects_sending_resets_for_not_existing_emails(self):
        response = self.client.post(reverse('authentication:send_reset_request'),
                                    {'email': 'John@example.com'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_rejects_sending_more_resets_than_limit(self):
        # 1 reset request per day
        user = User.objects.create_user(**classic_register_data)
        user.last_password_reset = timezone.now()
        user.email_verified = True
        user.save()
        response = self.client.post(reverse('authentication:send_reset_request'),
                                    {'email': 'John@example.com'}, format='json')
        self.assertEqual(response.status_code, 429)
        self.assertEqual(len(mail.outbox), 0)

    def test_resets_password_for_valid_tokens(self):
        user = User.objects.create_user(**classic_register_data)
        token = user.get_auth_jwt()
        user.current_reset_token = token
        user.save()
        reset_data = {'token': token, 'password': 'newPw'}
        response = self.client.post(reverse('authentication:complete_reset'), reset_data, format='json')
        user = User.objects.get(pk=user.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(user.check_password(reset_data['password']))

    def test_rejects_resets_for_invalid_tokens(self):
        response = self.client.post(reverse('authentication:complete_reset'),
                                    {'token': 'invalid', 'password': 'newPw'}, format='json')
        self.assertEqual(response.status_code, 401)

    def test_rejects_resets_for_non_existing_users(self):
        user = User.objects.create_user(**classic_register_data)
        token = user.get_auth_jwt()
        user.delete()
        reset_data = {'token': token, 'password': 'newPw'}
        response = self.client.post(reverse('authentication:complete_reset'), reset_data, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(User.objects.count(), 0)

    def test_rejects_resets_for_expired_token(self):
        user = User.objects.create_user(**classic_register_data)
        token = generate_test_token({'email': user.email})
        user.current_reset_token = token
        user.save()
        reset_data = {'token': token, 'password': 'newPw'}
        response = self.client.post(reverse('authentication:complete_reset'), reset_data, format='json')
        user = User.objects.get(pk=user.pk)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(user.check_password(reset_data['password']))

    def test_rejects_reset_for_used_tokens(self):
        user = User.objects.create_user(**classic_register_data)
        token = user.get_auth_jwt()
        user.current_reset_token = token
        user.save()
        reset_data = {'token': token, 'password': 'newPw'}
        response = self.client.post(reverse('authentication:complete_reset'), reset_data, format='json')
        user = User.objects.get(pk=user.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(user.check_password(reset_data['password']))
        new_reset_data = {'token': token, 'password': 'newPw2'}
        response = self.client.post(reverse('authentication:complete_reset'), new_reset_data, format='json')
        user = User.objects.get(pk=user.pk)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(user.check_password(new_reset_data['password']))


class AuthLogin(APITestCase):
    def test_login_social_user(self):
        register_data = {
            **classic_register_data,
            'social_id': '1234-1234',
            'social_picture': 'http://pic_url/',
            'password': None
        }
        user = User.objects.create_user(**register_data)
        response = self.client.post(reverse('authentication:login_user'),
                                    {'email': register_data['email'], 'withProvider': True}, format='json')
        self.assertIsNotNone(user.social_id)
        self.assertEqual(response.status_code, 200)

    def test_creates_user_on_login_with_provider(self):
        login_data = {
            **classic_register_data,
            'social_id': '1234-1234',
            'social_picture': 'http://pic_url/',
            'withProvider': True,
            'password': None
        }
        response = self.client.post(reverse('authentication:login_user'), login_data, format='json')
        users = User.objects.all()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(users.count(), 1)
        self.assertEqual(users[0].email, 'John@example.com')

    def test_login_user_with_valid_credits_and_verified_email(self):
        user = User.objects.create_user(**classic_register_data)
        user.email_verified = True
        user.save()
        login_data = {'email': user.email, 'password': classic_register_data['password']}
        response = self.client.post(reverse('authentication:login_user'), login_data, format='json')
        self.assertEqual(response.status_code, 200)

    def test_ignores_users_with_providers_on_classic_login(self):
        register_data = {
            **classic_register_data,
            'social_id': '1234-1234',
            'social_picture': 'http://pic_url/',
            'password': None
        }
        user = User.objects.create_user(**register_data)
        login_data = {'email': user.email, 'password': None}
        response = self.client.post(reverse('authentication:login_user'), login_data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_denies_login_when_email_not_verified(self):
        user = User.objects.create_user(**classic_register_data)
        login_data = {'email': user.email, 'password': classic_register_data['password']}
        response = self.client.post(reverse('authentication:login_user'), login_data, format='json')
        self.assertFalse(user.email_verified)
        self.assertEqual(response.status_code, 403)

    def test_denies_login_of_suspended_users(self):
        user = User.objects.create_user(**classic_register_data)
        user.email_verified = True
        user.is_active = False
        user.save()
        login_data = {'email': user.email, 'password': classic_register_data['password']}
        response = self.client.post(reverse('authentication:login_user'), login_data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_limits_login_attempts(self):
        from django.core.cache import cache
        throttling_rate = 30
        login_data = {'email': 'email@example.com', 'password': '1234'}
        for attempt in range(throttling_rate):
            self.client.post(reverse('authentication:login_user'), login_data, format='json')
        response = self.client.post(reverse('authentication:login_user'), login_data, format='json')
        self.assertEqual(response.status_code, 429)
        # clear the cache at the end to reset the login attempts in the rest of tests
        cache.clear()


class AuthUpdate(APITestCase):

    def test_updates_user_information(self):
        user = User.objects.create_user(**classic_register_data)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.token()}')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Smith')
        update_data = {'first_name': 'Joe', 'last_name': 'Nash', 'email': user.email}
        response = self.client.post(reverse('authentication:update_user', args=[user.pk]), update_data, format='json')
        user = User.objects.get(pk=user.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.first_name, 'Joe')
        self.assertEqual(user.last_name, 'Nash')

    def test_sends_verification_email_before_updating_email(self):
        user = User.objects.create_user(**classic_register_data)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.token()}')
        self.assertEqual(user.email, 'John@example.com')
        update_data = {'first_name': user.first_name, 'last_name': user.last_name, 'email': 'New@example.com'}
        response = self.client.post(reverse('authentication:update_user', args=[user.pk]), update_data, format='json')
        user = User.objects.get(pk=user.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.email, 'John@example.com')
        self.assertEqual(user.temp_email, 'New@example.com')
        self.assertEqual(len(mail.outbox), 1)

    def test_checks_if_new_email_exists(self):
        exists_register_data = {**classic_register_data, 'email': 'Exists@example.com'}
        User.objects.create_user(**exists_register_data)
        user = User.objects.create_user(**classic_register_data)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.token()}')
        self.assertEqual(user.email, 'John@example.com')
        update_data = {'first_name': user.first_name, 'last_name': user.last_name, 'email': 'Exists@example.com'}
        response = self.client.post(reverse('authentication:update_user', args=[user.pk]), update_data, format='json')
        user = User.objects.get(pk=user.pk)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(user.email, 'John@example.com')
        self.assertIsNone(user.temp_email)
        self.assertEqual(len(mail.outbox), 0)

    def test_updates_author_information(self):
        user = User.objects.create_user(**classic_register_data)
        user.author.nickname = 'Johnny'
        user.author.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.token()}')
        self.assertEqual(user.author.nickname, 'Johnny')
        self.assertEqual(user.author.social, {'fb': None, 'insta': None, 'twitter': None})
        update_social = {'fb': 'facebook.com/username', 'insta': None, 'twitter': None}
        update_data = {'author': {'nickname': 'Max', 'social': update_social}}
        response = self.client.post(reverse('authentication:update_author', args=[user.pk]), update_data, format='json')
        user = User.objects.get(pk=user.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(user.author.nickname, 'Max')
        self.assertEqual(user.author.social, update_social)

    def test_updates_password_with_correct_current(self):
        user = User.objects.create_user(**classic_register_data)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.token()}')
        update_data = {'password': 'newPassword', 'currentPassword': '1234'}
        response = self.client.post(reverse('authentication:update_security', args=[user.pk]),
                                    update_data, format='json')
        user = User.objects.get(pk=user.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(user.check_password('newPassword'))

    def test_updates_password_with_incorrect_current(self):
        user = User.objects.create_user(**classic_register_data)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.token()}')
        update_data = {'password': 'newPassword', 'currentPassword': '12345'}
        response = self.client.post(reverse('authentication:update_security', args=[user.pk]),
                                    update_data, format='json')
        user = User.objects.get(pk=user.pk)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(user.check_password('newPassword'))
        self.assertTrue(user.check_password('1234'))


class AuthFetch(APITestCase):

    def test_fetches_and_orders_authors_correctly(self):
        story = create_test_story()
        story2 = create_test_story(email='my@email.com')
        story3 = create_test_story(email='ex@example.com')
        story.author.followers.add(story2.author.user)
        story2.author.followers.add(story.author.user, story3.author.user)
        response = self.client.get(reverse('authentication:authors'))
        results = response.data['results']
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['user']['pk'], story2.author.user.pk)
        self.assertEqual(results[1]['user']['pk'], story.author.user.pk)

    def test_filters_authors_with_trigram_correctly(self):
        story = create_test_story(email='my@email.com')
        story2 = create_test_story()
        story.author.nickname = 'Derlaio'
        story.author.save()
        url = f"{reverse('authentication:authors')}?search=derly"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['nickname'], 'Derlaio')
        url = url.replace('nick', 'johnny')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['user']['fullname'], story2.author.user.fullname())


class AuthProfile(APITestCase):

    def test_fetches_profile(self):
        user = User.objects.create_user(**classic_register_data)
        response = self.client.get(reverse('authentication:profile', args=[user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['pk'], user.pk)

    def test_updates_profile_picture(self):
        user = User.objects.create_user(**classic_register_data)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.token()}')
        with open('stories/testImage.png', 'rb') as image:
            picture = SimpleUploadedFile('picture', image.read())
        response = self.client.post(reverse('authentication:update_media'), {'picture': picture, 'user': user.pk})
        self.assertEqual(response.status_code, 200)

    def test_updates_cover(self):
        user = User.objects.create_user(**classic_register_data)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.token()}')
        with open('stories/testImage.png', 'rb') as image:
            cover = SimpleUploadedFile('cover', image.read())
        response = self.client.post(reverse('authentication:update_media'), {'cover': cover, 'user': user.pk})
        self.assertEqual(response.status_code, 200)


class AuthDelete(APITestCase):

    def deletes_user_with_correct_password(self):
        user = User.objects.create_user(**classic_register_data)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.token()}')
        data = {'password': classic_register_data['password']}
        response = self.client.post(reverse('authentication:delete', args=[user.pk]), data, format='json')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(User.objects.count(), 0)

    def rejects_deleting_users_with_incorrect_password(self):
        user = User.objects.create_user(**classic_register_data)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.token()}')
        data = {'password': 'randomPassword'}
        response = self.client.post(reverse('authentication:delete', args=[user.pk]), data, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(User.objects.count(), 1)
