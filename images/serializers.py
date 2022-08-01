# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-31 15:59                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : serializers.py                                                    =
#    @Program: website                                                         =
# ==============================================================================

from rest_framework import serializers

from images.models import Image


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['created', 'url', 'id']

    url = serializers.ImageField(use_url=True, source='image')
