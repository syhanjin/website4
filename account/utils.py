# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-6-9 13:52                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : utils.py                                                          =
#    @Program: website4                                                        =
# ==============================================================================
import random
from datetime import datetime


def random_filename(name: str):
    ext = name.rsplit('.', maxsplit=1)[1]
    fn = f"{datetime.now().__format__('%Y%m%d%H%M%S%f')}{random.randint(0, 100)}"
    return f"{fn}.{ext}"
