# -*- coding: utf-8 -*-
# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-11 9:50                                                    =
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


class PerfectionManager(models.Manager):
    pass


class PerfectionStudentManager(PerfectionManager):
    pass


class PerfectionTeacherManager(PerfectionManager):
    pass


class PerfectionRoleChoice(models.TextChoices):
    TEACHER = "teacher", "老师"
    STUDENT = "student", "学生"


class Perfection(models.Model):
    # class Meta:
    #     ordering = ['created']

    # role = models.CharField(choices=PerfectionRoleChoice.choices, max_length=32)

    # last = models.DateTimeField(verbose_name="上一次打卡时间")
    REQUIRED_FIELDS = []
    SUMMARY_FIELDS = ['user']

    def __unicode__(self):
        return self.user.name + '_PERFECTION'


class PerfectionStudent(models.Model):
    id = models.UUIDField(verbose_name="编号", primary_key=True, default=uuid.uuid4, editable=False, max_length=64)

    user = models.OneToOneField(to=User, related_name="perfection", on_delete=models.CASCADE)
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
    role = PerfectionRoleChoice.STUDENT
    objects = PerfectionStudentManager()

    SUMMARY_FIELDS = [
        'user', 'role',
        'unremembered_words', 'reviewing_words', 'remembered_words', 'word_libraries'
    ]

    def __unicode__(self):
        return self.user.name + '_PERFECTION'

    def get_review_words(self) -> list:
        # 因为不太会搞只能用这种比较贵的方法
        rel = []
        for word in self.reviewing_words.all():
            if word.need_to_review:
                rel.append(word)
        return rel

    # 以下内容在多次调用时可以优化，暂时不进行优化
    @property
    def last_words_finished(self):
        latest = self.words.all().order_by("-finished").first()
        return getattr(latest, 'finished', None)

    @property
    def can_add_words_perfection(self):
        latest = self.get_latest(self.words)
        if latest is None:
            return True
        if not latest.is_finished:
            return False
        return latest.created.date() != timezone.now().date()

    @property
    def missed_words_perfection(self):
        latest = self.get_latest(self.words)
        if latest is None:
            return False
        return (not latest.is_finished) and latest.created.date() != timezone.now().date()

    @property
    def can_update_words_perfection(self):
        latest = self.get_latest(self.words)
        if latest is None:
            return False
        return (not latest.is_finished) and latest.updated.date() != timezone.now().date()

    @property
    def has_unfinished_words_perfection(self):
        latest = self.get_latest(self.words)
        if latest is None:
            return False
        return not latest.is_finished

    @staticmethod
    def get_latest(model):
        return model.all().order_by("-created").first()
