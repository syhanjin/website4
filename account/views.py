# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-25 14:41                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : views.py                                                          =
#    @Program: website                                                         =
# ==============================================================================

from django.contrib.auth import get_user_model
from djoser import utils
from djoser.compat import get_user_email
from djoser.conf import settings
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from account import serializers
from utils import random_filename

User = get_user_model()


class UserViewSet(BaseUserViewSet):

    def get_queryset(self):
        user = self.request.user
        queryset = super(viewsets.ModelViewSet, self).get_queryset()
        if settings.HIDE_USERS and self.action == "list" and user.admin == 0:
            queryset = queryset.filter(pk=user.pk)
        return queryset

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
        avatar_addr = user.avatar.url
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

    @action(["post"], detail=False)
    def reset_password_confirm(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.user.set_password(serializer.data["new_password"])
        serializer.user.save()

        if settings.TOKEN_MODEL:
            settings.TOKEN_MODEL.objects.filter(user=serializer.user).delete()

        if settings.PASSWORD_CHANGED_EMAIL_CONFIRMATION:
            context = {"user": serializer.user}
            to = [get_user_email(serializer.user)]
            settings.EMAIL.password_changed_confirmation(self.request, context).send(to)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TokenDestroyView(views.APIView):
    """
    Use this endpoint to logout user (remove user authentication token).
    """

    permission_classes = settings.PERMISSIONS.token_destroy

    def post(self, request):
        utils.logout_user(request)
        _cid = request.data.get("cid")
        if _cid:
            # 需要销毁cid
            request.user.cids.filter(cid=_cid).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
