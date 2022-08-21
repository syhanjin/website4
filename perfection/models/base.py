# -*- coding: utf-8 -*-
# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-21 18:22                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : base.py                                                           =
#    @Program: website                                                         =
# ==============================================================================
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class PerfectionStudentManager(models.Manager):
    pass


class PerfectionStudent(models.Model):
    id = models.UUIDField(verbose_name="编号", primary_key=True, default=uuid.uuid4, editable=False, max_length=64)

    user = models.OneToOneField(to=User, related_name="perfection_student", on_delete=models.CASCADE)
    teachers = models.ManyToManyField('perfection.PerfectionTeacher', related_name="students")
    # 单词打卡部分
    remembered_words = models.ManyToManyField(
        'perfection.WordPerfection', verbose_name="完成词库", related_name='remembered_perfection'
    )
    reviewing_words = models.ManyToManyField(
        'perfection.WordPerfection', verbose_name="复习词库", related_name='reviewing_perfection'
    )
    unremembered_words = models.ManyToManyField(
        'perfection.WordPerfection', verbose_name="保持词库", related_name='unremembered_perfection'
    )
    word_libraries = models.ManyToManyField(
        'perfection.WordLibrary', verbose_name="未记词库", related_name='libraries_perfection'
    )
    # words = models.ManyToManyField(WordsPerfection, verbose_name="打卡", related_name="perfection")
    # role = models.CharField(
    #     choices=PerfectionRoleChoice.choices, default=PerfectionRoleChoice.STUDENT, max_length=32, editable=False
    # )
    role = 'student'
    objects = PerfectionStudentManager()

    SUMMARY_FIELDS = [
        'user', 'role',
        'unremembered_words', 'reviewing_words', 'remembered_words', 'word_libraries'
    ]

    def __unicode__(self):
        return self.user.name + '_PERFECTION'

    # 以下内容在多次调用时可以优化，暂时不进行优化
    def get_review_words(self) -> list:
        # 因为不太会搞只能用这种比较贵的方法
        rel = []
        for word in self.reviewing_words.all():
            if word.need_to_review:
                rel.append(word)
        return rel

    @property
    def missed_words_perfection(self):
        latest = self.get_latest(self.words)
        if latest is None:
            return False
        return not latest or ((not latest.is_finished) and latest.created.date() != timezone.now().date())

    @property
    def has_unfinished_words_perfection(self):
        latest = self.get_latest(self.words)
        return not latest or (not latest.is_finished)

    @staticmethod
    def get_latest(model):
        return model.all().order_by("-created").first()


class RatingChoice(models.TextChoices):
    PASS = "pass", "通过"
    FAIL = "fail", "不通过"
