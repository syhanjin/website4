# -*- coding: utf-8 -*-
# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-11-20 9:19                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : teacher.py                                                        =
#    @Program: website                                                         =
# ==============================================================================
import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


# class PerfectionTeacherManager(models.Manager):
#     pass


class PerfectionTeacher(models.Model):
    id = models.UUIDField(verbose_name="编号", primary_key=True, default=uuid.uuid4, editable=False, max_length=64)
    user = models.OneToOneField(to=User, related_name="perfection_teacher", on_delete=models.CASCADE)

    role = 'teacher'
    # objects = PerfectionTeacherManager()
    SUMMARY_FIELDS = [
        'user', 'role',
    ]

    def __unicode__(self):
        return self.user.name + '_PERFECTION'
