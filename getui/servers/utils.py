# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-10 12:1                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : utils.py                                                          =
#    @Program: website                                                         =
# ==============================================================================

from django.conf import settings
from django.utils import timezone


def build_url(path):
    return settings.GETUI_BASE_URL + settings.APP_ID + path


def build_headers(token=None):
    headers = {
        'content-type': 'application/json;charset=utf-8'
    }
    if token is not None:
        headers['token'] = token
    return headers


def get_timestamp():
    return str(int(round(timezone.now().timestamp() * 1000)))
