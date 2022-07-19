# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-19 17:59                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : views.py                                                          =
#    @Program: website                                                         =
# ==============================================================================

from django.contrib.auth import get_user_model
from djoser.conf import settings
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from account import serializers
from account.utils import random_filename

User = get_user_model()


class UserViewSet(UserViewSet):
    def get_permissions(self):
        if self.action == 'set_avatar':
            self.permission_classes = settings.PERMISSIONS.set_avatar
        if self.action == 'set_signature':
            self.permission_classes = settings.PERMISSIONS.set_signature
        # if self.action == 'get_avatar':
        #     self.permission_classes = settings.PERMISSIONS.get
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'set_avatar':
            return serializers.UserSetAvatarSerializer
        elif self.action == 'set_signature':
            return serializers.UserSetSignatureSerializer
        return super().get_serializer_class()

    @action(["post"], detail=False, url_path="set_avatar")
    def set_avatar(self, request, *args, **kwargs):
        # serializer = self.get_serializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        user = self.request.user
        new_avatar = request.FILES['new_avatar']
        new_avatar.name = random_filename(new_avatar.name, ext="jpg")
        if user.avatar.name != 'avatar/default.jpg':
            user.avatar.delete()
        user.avatar = new_avatar
        user.save()
        avatar_addr = user.get_avatar_url()
        return Response(data={'avatar': avatar_addr}, status=status.HTTP_200_OK)

    @action(["post"], detail=False, url_path="set_signature")
    def set_signature(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user
        new_signature = request.data["new_signature"]
        user.signature = new_signature
        user.save()
        return Response(data={'signature': user.signature}, status=status.HTTP_200_OK)
