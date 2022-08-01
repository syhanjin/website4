# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-25 16:7                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : urls.py                                                           =
#    @Program: website                                                         =
# ==============================================================================
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework import routers

import account.views
import basis.views
import perfection.views

router = routers.DefaultRouter()
router.register(r'users', account.views.UserViewSet)
router.register(r'notice', basis.views.NoticeViewSet)
router.register(r'perfection/student', perfection.views.PerfectionStudentViewSet)
router.register(r'perfection/words', perfection.views.WordsPerfectionViewSet)
urlpatterns = [  # 管理员系统
    # re_path(r'^admin/', admin.site.urls), # 自己搭一个，这个不用了
]
urlpatterns += [  # api
    # path("api/v1/", include("djoser.urls")),
    path(settings.BASE_URL, include("djoser.urls.authtoken")),
    path(settings.BASE_URL, include(router.urls)),
]

# 媒体静态文件 设计成由django处理但是不由django路由
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 页面
# urlpatterns += [
#     re_path(r'^.*$', TemplateView.as_view(template_name="index.html"))
# ]
