# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-19 18:0                                                    =
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
