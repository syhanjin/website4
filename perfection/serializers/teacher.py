# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-16 17:5                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : teacher.py                                                        =
#    @Program: website                                                         =
# ==============================================================================

from rest_framework import serializers

from perfection.models.teacher import PerfectionTeacher


class PerfectionTeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfectionTeacher
        fields = PerfectionTeacher.SUMMARY_FIELDS


class PerfectionTeacherCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfectionTeacher
        fields = ['user']
