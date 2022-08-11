# -*- coding: utf-8 -*-
# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-11 9:22                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : auth.py                                                           =
#    @Program: website                                                         =
# ==============================================================================
import hashlib
from datetime import datetime, timedelta

import httpx as httpx
from django.conf import settings
from django.utils import timezone

from getui.models import Token
from .utils import build_headers, build_url, get_timestamp


def _update_token():
    url = build_url('/auth')
    timestamp = get_timestamp()
    sign = hashlib.sha256((settings.APP_KEY + timestamp + settings.MASTER_SECRET).encode('utf-8')).hexdigest()
    with httpx.Client() as client:
        r = client.post(
            url, json={
                "sign": sign,
                "timestamp": timestamp,
                "appkey": settings.APP_KEY
            },
            headers=build_headers()
        )
        resp = r.json()
        if resp["code"] == 0:
            data = resp['data']
            expire_time = datetime.fromtimestamp(int(data['expire_time']) / 1000)
            token_str = data['token']
            token = Token.objects.create(expire_time=expire_time, token=token_str)
            return token
        else:
            raise RuntimeError(resp)


def _get_token() -> Token:
    now = timezone.now()
    # 先清理过期或将要过期的token
    Token.objects.filter(expire_time__lte=now + timedelta(minutes=30)).delete()
    token = Token.objects.first()  # 获取最新的token
    if not token:
        token = _update_token()
    return token


def get_token_str():
    return _get_token().token


def get_token_expire_time():
    return _get_token().expire_time


def delete_token(token):
    url = build_url(f'/auth/{token}')
    with httpx.Client() as client:
        r = client.delete(url, headers=build_headers())
        resp = r.json()
        if resp['code'] == 0:
            Token.objects.filter(token=token).delete()
            return True
        else:
            return False
