# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2023 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2023-2-5 15:17                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : chWords.py                                                        =
#    @Program: website                                                         =
# ==============================================================================
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from images.serializers import ImageSerializer
from perfection.models.chWords import ChWordLibrary, ChWordPerfection, ChWordsPerfection


class ChWordsPerfectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChWordsPerfection
        fields = ChWordsPerfection.SUMMARY_FIELDS + ['acc_str', 'acc', 'user']

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


class ChWordsPerfectionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChWordsPerfection
        fields = ['id', 'updated', 'status', 'acc']

    acc = serializers.SerializerMethodField(read_only=True)

    def get_acc(self, obj):
        return obj.accuracy


class ChWordPerfectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChWordPerfection
        fields = '__all__'

    chWord = serializers.SerializerMethodField(read_only=True)

    def get_chWord(self, obj):
        return {
            'key': obj.chWord.key,
            'sentence': obj.chWord.sentence,
            'value': obj.chWord.value,
        }


class ChWordPerfectionSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChWordPerfection
        fields = ['key', 'sentence', 'value']

    key = serializers.CharField(source='chWord.key')
    sentence = serializers.CharField(source='chWord.sentence')
    value = serializers.CharField(source='chWord.value')


class ChWordsPerfectionRememberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChWordsPerfection
        fields = ['updated', 'remember']

    remember = ChWordPerfectionSimpleSerializer(many=True)


class ChWordsPerfectionUnrememberedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChWordsPerfection
        fields = ['updated', 'unremembered']

    unremembered = ChWordPerfectionSimpleSerializer(many=True)


class ChWordsPerfectionReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChWordsPerfection
        fields = ['updated', 'review']

    review = ChWordPerfectionSimpleSerializer(many=True)


class ChWordsPerfectionAdditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChWordsPerfection
        fields = ['updated', 'addition']

    addition = ChWordPerfectionSimpleSerializer(many=True)


class ChWordsPerfectionAllChWordsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChWordsPerfection
        fields = ['updated', 'remember', 'review', 'addition']

    remember = ChWordPerfectionSimpleSerializer(many=True)
    review = ChWordPerfectionSimpleSerializer(many=True)
    addition = ChWordPerfectionSimpleSerializer(many=True)


class ChWordLibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChWordLibrary
        fields = ['id', 'name', 'is_default', 'total']

    total = serializers.SerializerMethodField(read_only=True)

    def get_total(self, obj):
        return obj.chWords.count()


class ChWordsPerfectionFinishSerializer(serializers.ModelSerializer):
    # remember = serializers.ListField(child=serializers.BooleanField())
    # review = serializers.ListField(child=serializers.BooleanField())
    # remember = serializers.DictField(child=serializers.BooleanField())
    review = serializers.DictField(child=serializers.BooleanField())
    addition = serializers.DictField(child=serializers.BooleanField())
    picture = serializers.ListField(child=Base64ImageField(), max_length=3, min_length=1)

    class Meta:
        model = ChWordsPerfection
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
