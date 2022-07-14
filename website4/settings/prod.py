# -*- coding: utf-8 -*-
"""
Django settings for website4 project DEVELOP.

Generated by 'django-admin startproject' using Django 4.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-14 16:52                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : prod.py                                                           =
#    @Program: website                                                         =
# ==============================================================================

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("WEBSITE_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'account',
    'basis',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'djoser',
    'corsheaders',
    'imagekit',
]

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
    ]
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'website4.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['appfront/dist'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'website4.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'website4',
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators


AUTHENTICATION_BACKENDS = (
    'account.auth.UserBackend',
)

AUTH_USER_MODEL = 'account.User'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    # os.path.join(BASE_DIR, "appfront/dist/static"),
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

DJOSER = {
    'SITE_NAME': 'Sakuyark',
    'SEND_ACTIVATION_EMAIL': True,
    'ACTIVATION_URL': 'activation/{uid}/{token}',
    "SERIALIZERS": {
        "current_user": "account.serializers.UserSerializer",
    },
    "PERMISSIONS":
        {
            "activation": ["rest_framework.permissions.AllowAny"],
            "password_reset": ["rest_framework.permissions.AllowAny"],
            "password_reset_confirm": ["rest_framework.permissions.AllowAny"],
            "set_password": ["djoser.permissions.CurrentUserOrAdmin"],
            "username_reset": ["rest_framework.permissions.AllowAny"],
            "username_reset_confirm": ["rest_framework.permissions.AllowAny"],
            "set_username": ["djoser.permissions.CurrentUserOrAdmin"],
            "set_avatar": ["djoser.permissions.CurrentUserOrAdmin"],
            "set_signature": ["djoser.permissions.CurrentUserOrAdmin"],
            "user_create": ["rest_framework.permissions.AllowAny"],
            "user_delete": ["djoser.permissions.CurrentUserOrAdmin"],
            "user": ["djoser.permissions.CurrentUserOrAdmin"],
            "user_list": ["djoser.permissions.CurrentUserOrAdmin"],
            "token_create": ["rest_framework.permissions.AllowAny"],
            "token_destroy": ["rest_framework.permissions.IsAuthenticated"],
            # 直接对djoser的权限进行扩展
            "notice": ["rest_framework.permissions.AllowAny"],
            "notice_create": ["account.permissions.Admin"],
            "notice_methods": ["account.permissions.Admin"],
        }

}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.163.com"
EMAIL_PORT = 25
EMAIL_HOST_USER = "Sakuyark@163.com"
EMAIL_HOST_PASSWORD = ""
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_FROM = "Sakuyark"

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

BASE_URL = "api/v1/"
