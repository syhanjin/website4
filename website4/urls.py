# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2023 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2023-3-26 9:24                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : urls.py                                                           =
#    @Program: website                                                         =
# ==============================================================================

import djoser.views
# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-9 11:28                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : urls.py                                                           =
#    @Program: website                                                         =
# ==============================================================================
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from rest_framework_nested import routers

import account.views
import basis.views
import getui.views
import perfection.views

router = routers.DefaultRouter()
router.register(r'users', account.views.UserViewSet)
router.register(r'notice', basis.views.NoticeViewSet)
router.register(r'app', basis.views.AppViewSet)
router.register(r'perfection/student', perfection.views.PerfectionStudentViewSet)
router.register(r'perfection/words', perfection.views.WordsPerfectionViewSet)
router.register(r'perfection/word_libraries', perfection.views.WordLibraryViewSet)
router.register(r'perfection/chIdioms', perfection.views.ChIdiomsPerfectionViewSet)
router.register(r'perfection/chIdiom_libraries', perfection.views.ChIdiomLibraryViewSet)
router.register(r'getui/cid', getui.views.CidViewSet)

urlpatterns = [  # 管理员系统
    # re_path(r'^admin/', admin.site.urls), # 自己搭一个，这个不用了
]
urlpatterns += [
    re_path(rf"^{settings.BASE_URL}token/login/?$", djoser.views.TokenCreateView.as_view(), name="login"),
    re_path(rf"^{settings.BASE_URL}token/logout/?$", account.views.TokenDestroyView.as_view(), name="logout"),
]
urlpatterns += [  # api
    # path("api/v1/", include("djoser.urls")),
    path(settings.BASE_URL, include(router.urls)),
]

# 媒体静态文件 设计成由django处理但是不由django路由
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 页面
# urlpatterns += [
#     re_path(r'^.*$', TemplateView.as_view(template_name="index.html"))
# ]
