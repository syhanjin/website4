"""
WSGI config for website4 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-6-7 9:47                                                     =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : wsgi.py                                                           =
#    @Program: website4                                                        =
# ==============================================================================

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website4.settings')

application = get_wsgi_application()
