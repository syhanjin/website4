# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-18 13:0                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : class_.py                                                         =
#    @Program: website                                                         =
# ==============================================================================

import shortuuid
from django.db import models


class PerfectionClassManager(models.Manager):
    pass


def _id(): return shortuuid.ShortUUID(alphabet="0123456789").random(8)


class PerfectionSubject(models.Model):
    id = models.CharField(primary_key=True, editable=False, unique=True, max_length=64)
    name = models.CharField(max_length=64)


class PerfectionClass(models.Model):
    class Meta:
        ordering = ['-created']

    id = models.CharField(verbose_name="班级id", primary_key=True, default=_id, editable=False, max_length=8)
    created = models.DateTimeField(verbose_name="创建时间", auto_now_add=True, editable=False)
    name = models.CharField(verbose_name="班级名称", max_length=64)
    students = models.ManyToManyField('perfection.PerfectionStudent', related_name='classes')
    teacher = models.ForeignKey('perfection.PerfectionTeacher', related_name='classes', on_delete=models.CASCADE)
    subject = models.ManyToManyField(PerfectionSubject, related_name='classes')
    objects = PerfectionClassManager()