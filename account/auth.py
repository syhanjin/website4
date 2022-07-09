# -*- coding: utf-8 -*-
from account.models import User


class UserBackend(object):

    def authenticate(self, request, name=None, username=None, password=None):
        try:
            user = User.objects.get(name=name or username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
            return user
        except User.DoesNotExist:
            return None
