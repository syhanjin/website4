# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-28 18:52                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : utils.py                                                          =
#    @Program: website                                                         =
# ==============================================================================
import random
from datetime import datetime


def random_filename(name: str, ext=None):
    _ext = ext or name.rsplit('.', maxsplit=1)[1]
    fn = f"{datetime.now().__format__('%Y%m%d%H%M%S%f')}{random.randint(0, 100)}"
    return f"{fn}.{_ext}"


def unique_random_str():
    return f"{random.randint(1000000, 9999999)}{datetime.now().__format__('%Y%m%d%H%M%S%f')}"
