# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-12 10:20                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : permissions.py                                                    =
#    @Program: website                                                         =
# ==============================================================================

from rest_framework.permissions import BasePermission

from .models import AdminChoices


class _Admin(BasePermission):

    def has_permission(self, admin, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.admin >= admin
        )


class Admin(_Admin):
    def has_permission(self, request, view):
        return super().has_permission(AdminChoices.NORMAL, request, view)


class AdminSuper(_Admin):
    def has_permission(self, request, view):
        return super().has_permission(AdminChoices.SUPER, request, view)


class AdminDeveloper(_Admin):
    def has_permission(self, request, view):
        return super().has_permission(AdminChoices.DEVELOPER, request, view)
