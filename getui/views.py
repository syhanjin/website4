# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-11 9:17                                                    =
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cid = serializer.validated_data['cid']
        # 当已存在绑定
        if Cid.objects.filter(user=user, cid=cid):
            return Response(status=status.HTTP_200_OK, data={})
        is_success, msg = bind_user(cid, user)
        if not is_success:
            raise ValidationError(f"cid绑定失败, msg: {msg}")
        Cid.objects.update_or_create(
            defaults={
                "user": user,
                "cid": cid
            },
            cid=cid
        )
        return Response(status=status.HTTP_200_OK, data={})
