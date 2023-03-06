# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2023 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2023-3-7 0:14                                                     =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : intervals.py                                                      =
#    @Program: website                                                         =
# ==============================================================================

from datetime import timedelta

INTERVAL_UNACCEPTED_0 = [
    timedelta(days=1),
    timedelta(days=7),
    timedelta(days=15)
]
INTERVAL_UNACCEPTED_0_COUNT = len(INTERVAL_UNACCEPTED_0)
INTERVAL_UNACCEPTED_1_ = [
    timedelta(days=1),
    timedelta(days=3),
    timedelta(days=7),
    timedelta(days=15),
    timedelta(days=30)
]
INTERVAL_UNACCEPTED_1__COUNT = len(INTERVAL_UNACCEPTED_1_)


def get_interval_count(obj):
    if obj.unaccepted == 0:
        return INTERVAL_UNACCEPTED_0_COUNT
    elif obj.unaccepted > 0:
        return INTERVAL_UNACCEPTED_1__COUNT


def get_next_interval(obj, t):
    if t == 0:
        # 为了加快滚动直接加入记忆版的，七天后再复习一次，这时known会被设为True，代表可能认识
        return timedelta(days=7)
    elif t == 1:
        # 加入记忆版，也就是说，今天记忆版的词明天复习
        return timedelta(days=1)
    elif t == 2:
        # 打卡版正确的词，需要更新total，correct
        if obj.known:
            # 如果被标记为认识，60天后再次复习（不会执行）
            return timedelta(days=60)
        if obj.unaccepted == 0:
            return INTERVAL_UNACCEPTED_0[obj.count]
        elif obj.unaccepted > 0:
            return INTERVAL_UNACCEPTED_1_[obj.count]
    else:
        raise ValueError()
