# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-18 16:1                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : base.py                                                           =
#    @Program: website                                                         =
# ==============================================================================

from rest_framework import serializers

from perfection.conf import settings
from perfection.models.base import PerfectionStudent
from perfection.models.words import WordLibrary


class PerfectionStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfectionStudent
        fields = PerfectionStudent.SUMMARY_FIELDS + [
            'has_unfinished_words_perfection',
            'has_missed_words_perfection'
        ]

    # 由于数据量太大，暂时关闭
    # unremembered_words = settings.SERIALIZERS.word_perfection(many=True)
    # remembered_words = settings.SERIALIZERS.word_perfection(many=True)
    # reviewing_words = settings.SERIALIZERS.word_perfection(many=True)
    user = serializers.SerializerMethodField(read_only=True)
    unremembered_words = serializers.SerializerMethodField(read_only=True)
    remembered_words = serializers.SerializerMethodField(read_only=True)
    reviewing_words = serializers.SerializerMethodField(read_only=True)

    word_libraries = settings.SERIALIZERS.word_library(many=True)

    has_unfinished_words_perfection = serializers.SerializerMethodField(read_only=True)
    has_missed_words_perfection = serializers.SerializerMethodField(read_only=True)

    def get_user(self, obj):
        return obj.user.name

    def get_unremembered_words(self, obj):
        return obj.unremembered_words.count()

    def get_remembered_words(self, obj):
        return obj.remembered_words.count()

    def get_reviewing_words(self, obj):
        return obj.reviewing_words.count()

    def get_has_unfinished_words_perfection(self, obj):
        latest = obj.get_latest(obj.words)
        if not latest:
            return False
        return not latest.is_finished

    def get_has_missed_words_perfection(self, obj):
        return obj.missed_words_perfection


class PerfectionStudentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfectionStudent
        fields = []

    pass


class PerfectionStudentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfectionStudent
        fields = '__all__'


class PerfectionStudentRememberedWordsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfectionStudent
        fields = ('remembered_words',)


class PerfectionStudentWordLibrariesSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfectionStudent
        fields = ('word_libraries',)

    word_libraries = serializers.ListField(child=serializers.UUIDField(), min_length=1)

    def validate_word_libraries(self, attr):
        if WordLibrary.objects.filter(id__in=attr).count() != len(attr):
            raise serializers.ValidationError("有不存在的词库")
        return attr
