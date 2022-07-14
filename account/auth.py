# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-12 10:20                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : auth.py                                                           =
#    @Program: website                                                         =
# ==============================================================================

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
