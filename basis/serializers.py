# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-15 12:25                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : serializers.py                                                    =
#    @Program: website                                                         =
# ==============================================================================
from rest_framework import serializers

from .models import Notice, NoticeTypeChoice


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

    def validate(self, attrs):
        return attrs

    def create(self, validated_data):
        return Notice.objects.create(**validated_data)


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
