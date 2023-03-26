# -*- coding: utf-8 -*-
# ==============================================================================
#  Copyright (C) 2023 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2023-3-26 9:56                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : base.py                                                           =
#    @Program: website                                                         =
# ==============================================================================
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from perfection.conf import settings

User = get_user_model()


class PerfectionStudentManager(models.Manager):
    pass


class PerfectionStudent(models.Model):
    id = models.UUIDField(verbose_name="编号", primary_key=True, default=uuid.uuid4, editable=False, max_length=64)

    user = models.OneToOneField(to=User, related_name="perfection_student", on_delete=models.CASCADE)
    # 单词打卡部分
    word_perfections = models.ManyToManyField(
        'perfection.WordPerfection', related_name="perfection_student"
    )
    word_libraries = models.ManyToManyField(
        'perfection.WordLibrary', verbose_name="单词词库", related_name='libraries_perfection'
    )

    chIdiom_perfections = models.ManyToManyField(
        'perfection.chIdiomPerfection', related_name="perfection_student"
    )
    chIdiom_libraries = models.ManyToManyField(
        'perfection.chIdiomLibrary', verbose_name="成语词库", related_name='libraries_perfection'
    )
    role = 'student'
    objects = PerfectionStudentManager()

    SUMMARY_FIELDS = [
        'id', 'user', 'role', 'word_libraries', 'chIdiom_libraries'
    ]

    def __unicode__(self):
        return self.user.name + '_PERFECTION'

    def get_review_words(self) -> QuerySet:
        return self.word_perfections.filter(
            status=settings.CHOICES.word_perfection_status.REVIEWING, next__lte=timezone.now()
        )

    def get_review_chIdioms(self) -> QuerySet:
        return self.chIdiom_perfections.filter(
            status=settings.CHOICES.chIdiom_perfection_status.REVIEWING, next__lte=timezone.now()
        )

    @property
    def missed_words_perfection(self):
        latest = self.get_latest(self.words)
        return not latest or (
                latest.status != settings.CHOICES.words_perfection_status.FINISHED
                and latest.created.date() < timezone.now().date()
        )

    @property
    def has_unfinished_words_perfection(self):
        latest = self.get_latest(self.words)
        return not latest or latest.status != settings.CHOICES.words_perfection_status.FINISHED

    @staticmethod
    def get_latest(model):
        return model.all().order_by("-updated").first()
