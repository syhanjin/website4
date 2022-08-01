# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-31 18:31                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : base.py                                                           =
#    @Program: website                                                         =
# ==============================================================================

from rest_framework import serializers

from perfection.conf import settings
from perfection.models.base import PerfectionStudent


class PerfectionStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfectionStudent
        fields = PerfectionStudent.SUMMARY_FIELDS + [
            'has_unfinished_words_perfection',
            'has_missed_words_perfection'
        ]

    unremembered_words = settings.SERIALIZERS.word_perfection(many=True)
    remembered_words = settings.SERIALIZERS.word_perfection(many=True)
    reviewing_words = settings.SERIALIZERS.word_perfection(many=True)

    has_unfinished_words_perfection = serializers.SerializerMethodField(read_only=True)
    has_missed_words_perfection = serializers.SerializerMethodField(read_only=True)

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
