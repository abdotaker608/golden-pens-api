from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):

    def _create_user(self, email, password=None, **extras):
        user = self.model(email=email, **extras)
        if password is not None:
            user.set_password(password)
            user.save()
        return user

    def create_user(self, email, password=None, **extras):
        return self._create_user(email, password, **extras)

    def create_superuser(self, email, password=None, **extras):
        extras.setdefault('is_staff', True)
        extras.setdefault('is_superuser', True)
        extras.setdefault('email_verified', True)
        return self._create_user(email, password, **extras)
