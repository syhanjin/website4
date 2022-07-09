# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-9 21:2                                                     =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : views.py                                                          =
#    @Program: website4                                                        =
# ==============================================================================
from djoser.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Notice
from .serializers import NoticeCreateSerializer, NoticeDeleteSerializer, NoticeDetailSerializer, NoticeSerializer


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
        elif self.action == 'delete':
            return NoticeDeleteSerializer
        elif self.action == 'retrieve':
            return NoticeDetailSerializer
        return NoticeSerializer

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = settings.PERMISSIONS.notice_create
        elif self.action == "delete":
            self.permission_classes = settings.PERMISSIONS.notice_delete
        elif self.action == "retrieve":
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

    @action(methods=['get'], detail=False)
    def delete(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notice = Notice.objects.filter(**serializer.data)
        notice.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
