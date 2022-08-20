# -*- coding: utf-8 -*-
# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-19 13:58                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : class_.py                                                         =
#    @Program: website                                                         =
# ==============================================================================
from rest_framework import serializers

from images.serializers import ImageSerializer
from perfection.conf import settings
from perfection.models.class_ import PerfectionClass, PerfectionSubject


class PerfectionSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfectionSubject
        fields = '__all__'


class PerfectionSubjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfectionSubject
        fields = ['id', 'name']

    id = serializers.CharField()

    def validate_id(self, attr):
        if PerfectionSubject.objects.filter(id=attr).count() > 0:
            raise serializers.ValidationError("subject 已存在")
        return attr


class PerfectionClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfectionClass
        fields = '__all__'

    teacher = serializers.SerializerMethodField(read_only=True)
    subject = PerfectionSubjectSerializer(many=True)
    students = serializers.SerializerMethodField(read_only=True)

    def get_teacher(self, obj):
        return {
            "uuid": obj.teacher.user.uuid,
            "name": obj.teacher.user.name,
        }

    def get_students(self, obj):
        return obj.students.count()


class PerfectionClassDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfectionClass
        fields = '__all__'

    # teacher = settings.SERIALIZERS.perfection_teacher()
    subject = PerfectionSubjectSerializer(many=True)
    # students = settings.SERIALIZERS.perfection_student(many=True)
    students = serializers.SerializerMethodField(read_only=True)

    def get_students(self, obj):
        return obj.students.count()


class PerfectionClassSubjectCheckSerializer(serializers.Serializer):
    # 为了少费点功夫
    id = serializers.UUIDField()
    rating = serializers.ChoiceField(settings.CHOICES.rating_choice.choices)


class PerfectionClassSubjectGetSerializer(serializers.Serializer):
    id = serializers.UUIDField()


class PerfectionClassWordsPerfectionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = settings.MODELS.words_perfection
        fields = settings.MODELS.words_perfection.SUMMARY_FIELDS + ['acc_str', 'user', 'unremembered',
                                                                    'remember', 'review']

    picture = ImageSerializer(many=True)
    acc_str = serializers.SerializerMethodField(read_only=True)
    user = serializers.CharField(source="perfection.user.name")
    unremembered = settings.SERIALIZERS.word_perfection_simple(many=True)
    remember = settings.SERIALIZERS.word_perfection_simple(many=True)
    review = settings.SERIALIZERS.word_perfection_simple(many=True)

    def get_acc_str(self, obj):
        return obj.accuracy_str

    def get_acc(self, obj):
        return obj.accuracy


class PerfectionClassCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfectionClass
        fields = ['name', 'subject']

    subject = serializers.ListField(child=serializers.CharField(), min_length=1)

    def validate_subject(self, attr):
        if PerfectionSubject.objects.filter(id__in=attr).count() < len(attr):
            raise serializers.ValidationError("具有不存在的项目")
        return attr
