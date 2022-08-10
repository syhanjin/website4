# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-10 20:52                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : views.py                                                          =
#    @Program: website                                                         =
# ==============================================================================

from djoser.conf import settings
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from getui.models import Cid
from getui.serializers import AuthCidSerializer, CidSerializer
from getui.servers.user import bind_user


class CidViewSet(viewsets.ModelViewSet):
    serializer_class = CidSerializer
    queryset = Cid.objects.all()
    permission_classes = settings.PERMISSIONS.user
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        return user.cids.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return AuthCidSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = settings.PERMISSIONS.user
        return super().get_permissions()

    def get_instance(self):
        return self.request.user

    def create(self, request, *args, **kwargs):
        user = self.get_instance()
        data = request.data.copy()
        data['user'] = user.pk
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        bound, msg = bind_user(serializer.validated_data['cid'], user)
        if not bound:
            raise ValidationError(f"cid绑定失败, msg: {msg}")
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
