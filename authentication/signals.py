
def initialize_user(user):
    from rest_framework.authtoken.models import Token
    from .models import Author

    # create an auth token and author object for each new user
    Token.objects.create(user=user)
    Author.objects.create(user=user)
