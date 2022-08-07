# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-31 17:51                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : words.py                                                          =
#    @Program: website                                                         =
# ==============================================================================
from django.forms import model_to_dict
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from images.serializers import ImageSerializer
from perfection.models.words import WordPerfection, WordsPerfection


class WordsPerfectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordsPerfection
        fields = WordsPerfection.SUMMARY_FIELDS + ['acc_str', 'acc']

    # picture = serializers.SerializerMethodField(read_only=True)
    picture = ImageSerializer(many=True)
    acc_str = serializers.SerializerMethodField(read_only=True)
    acc = serializers.SerializerMethodField(read_only=True)

    def get_acc_str(self, obj):
        return obj.accuracy_str

    def get_acc(self, obj):
        return obj.accuracy

    # def get_picture(self, obj):
    #     images = []
    #     for img in obj.picture.all():
    #         images.append(img.image.url)
    #     return images


class WordPerfectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordPerfection
        fields = '__all__'

    word = serializers.SerializerMethodField(read_only=True)

    def get_word(self, obj):
        return model_to_dict(obj.word)


class WordsPerfectionRememberSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordsPerfection
        fields = ['created', 'remember']

    remember = WordPerfectionSerializer(many=True)


class WordsPerfectionUnrememberedSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordsPerfection
        fields = ['created', 'unremembered']

    unremembered = WordPerfectionSerializer(many=True)


class WordsPerfectionReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordsPerfection
        fields = ['created', 'review']

    review = WordPerfectionSerializer(many=True)


class WordsPerfectionRememberAndReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordsPerfection
        fields = ['created', 'remember', 'review']

    remember = WordPerfectionSerializer(many=True)
    review = WordPerfectionSerializer(many=True)


class WordsPerfectionFinishSerializer(serializers.ModelSerializer):
    # remember = serializers.ListField(child=serializers.BooleanField())
    # review = serializers.ListField(child=serializers.BooleanField())
    # remember = serializers.DictField(child=serializers.BooleanField())
    review = serializers.DictField(child=serializers.BooleanField())
    picture = serializers.ListField(child=Base64ImageField(), max_length=3, min_length=1)

    class Meta:
        model = WordsPerfection
        fields = ['review', 'picture']

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