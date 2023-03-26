# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2023 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2023-3-26 9:22                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : chIdioms.py                                                       =
#    @Program: website                                                         =
# ==============================================================================
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from images.serializers import ImageSerializer
from perfection.models.chIdioms import ChIdiomLibrary, ChIdiomPerfection, ChIdiomsPerfection


class ChIdiomsPerfectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChIdiomsPerfection
        fields = ChIdiomsPerfection.SUMMARY_FIELDS + ['acc_str', 'acc', 'user']

    # picture = serializers.SerializerMethodField(read_only=True)
    picture = ImageSerializer(many=True)
    acc_str = serializers.SerializerMethodField(read_only=True)
    acc = serializers.SerializerMethodField(read_only=True)
    user = serializers.CharField(source="perfection.user.name")

    def get_acc_str(self, obj):
        return obj.accuracy_str

    def get_acc(self, obj):
        return obj.accuracy

    # def get_picture(self, obj):
    #     images = []
    #     for img in obj.picture.all():
    #         images.append(img.image.url)
    #     return images


class ChIdiomsPerfectionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChIdiomsPerfection
        fields = ['id', 'updated', 'status', 'acc']

    acc = serializers.SerializerMethodField(read_only=True)

    def get_acc(self, obj):
        return obj.accuracy


class ChIdiomPerfectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChIdiomPerfection
        fields = '__all__'

    chIdiom = serializers.SerializerMethodField(read_only=True)

    def get_chIdiom(self, obj):
        return {
            'key': obj.chIdiom.key,
            'value': obj.chIdiom.value,
        }


class ChIdiomPerfectionSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChIdiomPerfection
        fields = ['key', 'value']

    key = serializers.CharField(source='chIdiom.key')
    value = serializers.CharField(source='chIdiom.value')


class ChIdiomsPerfectionRememberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChIdiomsPerfection
        fields = ['updated', 'remember']

    remember = ChIdiomPerfectionSimpleSerializer(many=True)


class ChIdiomsPerfectionUnrememberedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChIdiomsPerfection
        fields = ['updated', 'unremembered']

    unremembered = ChIdiomPerfectionSimpleSerializer(many=True)


class ChIdiomsPerfectionReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChIdiomsPerfection
        fields = ['updated', 'review']

    review = ChIdiomPerfectionSimpleSerializer(many=True)


class ChIdiomsPerfectionAdditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChIdiomsPerfection
        fields = ['updated', 'addition']

    addition = ChIdiomPerfectionSimpleSerializer(many=True)


class ChIdiomsPerfectionAllChIdiomsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChIdiomsPerfection
        fields = ['updated', 'remember', 'review', 'addition']

    remember = ChIdiomPerfectionSimpleSerializer(many=True)
    review = ChIdiomPerfectionSimpleSerializer(many=True)
    addition = ChIdiomPerfectionSimpleSerializer(many=True)


class ChIdiomLibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChIdiomLibrary
        fields = ['id', 'name', 'is_default', 'total']

    total = serializers.SerializerMethodField(read_only=True)

    def get_total(self, obj):
        return obj.chIdioms.count()


class ChIdiomsPerfectionFinishSerializer(serializers.ModelSerializer):
    # remember = serializers.ListField(child=serializers.BooleanField())
    # review = serializers.ListField(child=serializers.BooleanField())
    # remember = serializers.DictField(child=serializers.BooleanField())
    review = serializers.DictField(child=serializers.BooleanField())
    addition = serializers.DictField(child=serializers.BooleanField())
    picture = serializers.ListField(child=Base64ImageField(), max_length=5, min_length=0)

    class Meta:
        model = ChIdiomsPerfection
        fields = ['review', 'addition', 'picture']

    def validate_picture(self, attr):
        for pic in attr:
            if not pic:
                raise serializers.ValidationError("打卡图片不可为空")
        return attr

    # def validate(self, attrs):
    #     errors = {}
    #     if not len(attrs['remember']) == attrs['remember_len']:
    #         # raise serializers.ValidationError("记忆版单词数量不匹配")
    #         errors['remember'] = '记忆版单词数量不匹配'
    #     if not len(attrs['review']) == attrs['review_len']:
    #         # raise serializers.ValidationError("测试版单词数量不匹配")
    #         errors['review'] = '测试版单词数量不匹配'
    #     if len(errors.keys()) > 0:
    #         raise serializers.ValidationError(errors)
    #     return attrs
