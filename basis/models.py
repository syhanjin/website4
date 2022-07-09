# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-9 18:23                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : models.py                                                         =
#    @Program: website4                                                        =
# ==============================================================================
import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


# 公告
class NoticeManager(models.Manager):
    pass


class NoticeTypeChoice(models.TextChoices):
    # POPUP = 'popup', 'Pop Up'
    TOP = 'top', 'Top'
    NORMAL = 'normal', 'Normal'


class Notice(models.Model):
    class Meta:
        ordering = ['-type', '-created']

    id = models.UUIDField(verbose_name="编号", primary_key=True, default=uuid.uuid4, editable=False, max_length=64)
    title = models.CharField(max_length=256, verbose_name='标题')
    content = models.CharField(max_length=100000, verbose_name='内容')
    author = models.ForeignKey(User, verbose_name='发布者', null=True, on_delete=models.SET_NULL)
    type = models.CharField(
        choices=NoticeTypeChoice.choices, default=NoticeTypeChoice.NORMAL, verbose_name='类型', max_length=16
    )
    created = models.DateTimeField(verbose_name="创建时间", auto_now_add=True, editable=False)

    objects = NoticeManager()
    REQUIRED_FIELDS = ['title', 'content', 'type']

    def reads(self):
        return NoticeRead.objects.filter(notice__id=self.id).count()

    def __unicode__(self):
        return self.title


class NoticeRead(models.Model):
    class Meta:
        pass

    notice = models.ForeignKey(Notice, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    objects = models.Manager()
