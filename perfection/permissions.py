# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-22 17:2                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : permissions.py                                                    =
#    @Program: website                                                         =
# ==============================================================================
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission

from account.permissions import AdminSuper


class NoPerfection(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "未开通打卡系统"


class _Perfection(BasePermission):

    def has_permission(self, request, view):
        # print(request.user)
        if not bool(
                request.user
                and request.user.is_authenticated
                and request.user.perfection
        ):
            raise NoPerfection
        return True

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.perfection
        )


class _Teacher(BasePermission):

    def has_permission(self, request, view):
        return request.user.perfection.role == 'teacher'

    def has_object_permission(self, request, view, obj):
        return request.user.perfection.role == 'teacher'


class _Student(BasePermission):

    def has_permission(self, request, view):
        return request.user.perfection.role == 'student'

    def has_object_permission(self, request, view, obj):
        return request.user.perfection.role == 'student'


class _Current(BasePermission):
    def has_object_permission(self, request, view, obj):
        # print(request.user.perfection.id != obj.p.id)
        return request.user.perfection.id != obj.p.id


Student = _Perfection & _Student
CurrentStudent = _Perfection & _Student & _Current
Teacher = _Perfection & _Teacher

StudentOrTeacher = Student | Teacher
StudentOrAdmin = Student | AdminSuper
TeacherOrAdmin = Teacher | AdminSuper
CurrentStudentOrTeacherOrAdmin = CurrentStudent | Teacher | AdminSuper
StudentOrTeacherOrAdmin = Student | Teacher | AdminSuper
# CurrentStudentOrCurrentTeacherOrAdmin = CurrentStudent | CurrentTeacher | AdminSuper
