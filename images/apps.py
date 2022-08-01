# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-30 19:54                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : apps.py                                                           =
#    @Program: website                                                         =
# ==============================================================================

from django.apps import AppConfig

"""
用于解决多图片上传问题
解决思路：用一个模型单独保存图片，用多对多连接，可以设置保存时长
"""


class ImagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'images'
