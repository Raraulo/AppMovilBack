from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None
