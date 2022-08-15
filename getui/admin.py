# Register your models here.

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-15 11:42                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : admin.py                                                          =
#    @Program: website                                                         =
# ==============================================================================
from datetime import timedelta

from django.utils import timezone

from getui.models import NotificationMessageOffline, NotificationMessageOnline

DURATION = timedelta(hours=24)


def clean_notifications():
    """
    每一条消息只在后台保存24小时
    :return:
    """
    now = timezone.now()
    NotificationMessageOnline.objects.filter(created__lt=now - DURATION).delete()
    NotificationMessageOffline.objects.filter(created__lt=now - DURATION).delete()
    pass
