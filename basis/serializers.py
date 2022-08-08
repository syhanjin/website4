# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-8 19:25                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : serializers.py                                                    =
#    @Program: website                                                         =
# ==============================================================================
from rest_framework import serializers

from .models import App, AppVersion, Notice, NoticeTypeChoice


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ('id', 'title', 'created', 'author', 'type')

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class NoticeCreateSerializer(serializers.ModelSerializer):
    title = serializers.CharField()
    content = serializers.CharField()
    type = serializers.ChoiceField(choices=NoticeTypeChoice.choices)

    class Meta:
        model = Notice
        fields = Notice.REQUIRED_FIELDS


class NoticeMethodsSerializer(serializers.ModelSerializer):
    # id = serializers.UUIDField()

    class Meta:
        model = Notice
        fields = ('id',)

    def validate_id(self, attr):
        if Notice.objects.filter(id=attr).count() == 0:
            raise serializers.ValidationError("指定公告不存在")
        return attr

    pass


class NoticeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = "__all__"

    author = serializers.SerializerMethodField(read_only=True)

    def get_author(self, obj):
        return {
            'name': obj.author.name,
            'uuid': obj.author.uuid
        }


class NoticeCountSerializer(serializers.ModelSerializer):
    pass


# app

class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = '__all__'

    author = serializers.SerializerMethodField(read_only=True)

    def get_author(self, obj):
        return {
            'name': obj.author.name,
            'uuid': obj.author.uuid
        }


class AppCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = App
        fields = ('name', 'description')


class AppVersionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = AppVersion.REQUIRED_FIELDS + ['app_id']

    app_id = serializers.UUIDField()
    is_force = serializers.ChoiceField(choices=['true', 'false'])
    apk = serializers.FileField()

    def validate_app_id(self, attr):
        if App.objects.filter(id=attr).count() > 0:
            return attr
        else:
            raise serializers.ValidationError("app不存在")


class AppSerializer(serializers.ModelSerializer):
    versions = AppVersionSerializer(many=True)

    class Meta:
        model = App
        fields = '__all__'
