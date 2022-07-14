# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-12 12:39                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : views.py                                                          =
#    @Program: website                                                         =
# ==============================================================================
from djoser.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Notice, NoticeTypeChoice
from .serializers import (
    NoticeCountSerializer, NoticeCreateSerializer, NoticeDetailSerializer,
    NoticeMethodsSerializer, NoticeSerializer,
)


# 公告
class NoticePagination(PageNumberPagination):
    # 默认的大小
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 10


class NoticeViewSet(viewsets.ModelViewSet):
    serializer_class = NoticeSerializer
    queryset = Notice.objects.all()
    permission_classes = settings.PERMISSIONS.notice
    lookup_field = 'id'
    pagination_class = NoticePagination

    def get_serializer_class(self):
        if self.action == 'create':
            return NoticeCreateSerializer
        elif self.action == 'delete' or self.action == 'change_type':
            return NoticeMethodsSerializer
        elif self.action == 'retrieve':
            return NoticeDetailSerializer
        elif self.action == 'count':
            return NoticeCountSerializer
        return NoticeSerializer

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = settings.PERMISSIONS.notice_create
        elif self.action == "delete" or self.action == 'change_type':
            self.permission_classes = settings.PERMISSIONS.notice_methods
        elif self.action == "retrieve":
            self.permission_classes = settings.PERMISSIONS.notice
        elif self.action == "count":
            self.permission_classes = settings.PERMISSIONS.notice
        return super().get_permissions()

    def get_instance(self):
        return self.request.user

    def create(self, request, *args, **kwargs):
        user = self.get_instance()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notice = serializer.save()
        notice.author = user
        notice.save()
        return Response(status=status.HTTP_200_OK, data={'id': notice.id})

    # def get(self):

    @action(methods=['post'], detail=False)
    def delete(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notice = Notice.objects.filter(id__in=request.data.get('id'))
        notice.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get', 'post'], detail=False)
    def count(self, request, *args, **kwargs):
        count = Notice.objects.all().count()
        return Response(status=status.HTTP_200_OK, data={'count': count})

    @action(methods=['post'], detail=False)
    def change_type(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notice = Notice.objects.filter(**serializer.data).first()
        if notice.type == NoticeTypeChoice.TOP:
            notice.type = NoticeTypeChoice.NORMAL
        else:
            notice.type = NoticeTypeChoice.TOP
        notice.save()
        return Response(status=status.HTTP_200_OK, data={'type': notice.type})
