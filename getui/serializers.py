# -*- coding: utf-8 -*-
# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-11 9:10                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : serializers.py                                                    =
#    @Program: website                                                         =
# ==============================================================================
from rest_framework import serializers

from getui.models import Cid


class AuthCidSerializer(serializers.Serializer):
    cid = serializers.CharField(min_length=32, max_length=32)


class CidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cid
        fields = '__all__'

    user = serializers.SerializerMethodField(read_only=True)

    def get_user(self, obj):
        return {
            "uuid": obj.user.uuid,
            "name": obj.user.name
        }
