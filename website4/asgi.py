"""
ASGI config for website4 project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-6-7 9:47                                                     =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : asgi.py                                                           =
#    @Program: website4                                                        =
# ==============================================================================

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website4.settings')

application = get_asgi_application()
