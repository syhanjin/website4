# ==============================================================================
#  Copyright (C) 2023 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2023-1-29 18:41                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : views.py                                                          =
#    @Program: website                                                         =
# ==============================================================================
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .conf import settings
from .models import App, AppVersion, Notice, NoticeTypeChoice
from .serializers import (
    AppCreateSerializer, AppSerializer, AppVersionCreateSerializer, AppVersionSerializer, NoticeCountSerializer,
    NoticeCreateSerializer,
    NoticeDetailSerializer,
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
        return super().get_serializer_class()

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


# app
class AppViewSet(viewsets.ModelViewSet):
    serializer_class = AppSerializer
    queryset = App.objects.all()
    permission_classes = settings.PERMISSIONS.app
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'create':
            return AppCreateSerializer
        elif self.action == 'version_create':
            return AppVersionCreateSerializer
        elif self.action == 'latest':
            return AppVersionSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = settings.PERMISSIONS.app_create
        elif self.action == "version_create":
            self.permission_classes = settings.PERMISSIONS.app_version_create
        return super().get_permissions()

    def get_instance(self):
        return self.request.user

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        app = serializer.save()
        return Response(
            status=status.HTTP_200_OK, data={
                'app_id': app.id
            }
        )

    @action(methods=['post'], detail=False)
    def version_create(self, request, *args, **kwargs):
        user = self.get_instance()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        app = App.objects.get(id=data['app_id'])
        apk = data['apk']
        apk.name = f"{app.name}-{data['version_name']}.apk"
        version = AppVersion.objects.create(
            app=app,
            version_name=data['version_name'],
            version_code=data['version_code'],
            updates=data['updates'],
            is_force=data['is_force'] == 'true',
            author=user,
            apk=apk,
        )
        return Response(status=status.HTTP_200_OK, data={'apk': request.build_absolute_uri(version.apk.url)})

    @action(methods=['get'], detail=True)
    def latest(self, request, *args, **kwargs):
        app = self.get_object()
        latest = self.get_serializer(instance=app.versions.all().first())
        data = latest.data
        VersionCode = request.query_params.get('VersionCode')
        if VersionCode:
            data["updates"] = ""
            for version in app.versions.filter(version_code__gt=VersionCode):
                if version.is_force:
                    data["is_force"] = True
                data["updates"] += f"# {version.version_name}\n{version.updates}"

        return Response(status=status.HTTP_200_OK, data=data)
