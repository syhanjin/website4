# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-7-28 20:58                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : conf.py                                                           =
#    @Program: website                                                         =
# ==============================================================================

from django.conf import settings as django_settings
from django.core.signals import setting_changed
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string

PERFECTION_SETTINGS_NAMESPACE = "PERFECTION"


class ObjDict(dict):
    def __getattribute__(self, item):
        try:
            val = self[item]
            if isinstance(val, str):
                val = import_string(val)
            elif isinstance(val, (list, tuple)):
                val = [import_string(v) if isinstance(v, str) else v for v in val]
            self[item] = val
        except KeyError:
            val = super(ObjDict, self).__getattribute__(item)

        return val


default_settings = {

    "PERMISSIONS": ObjDict(
        {
            "student": ['perfection.permissions.StudentOrTeacherOrAdmin'],
            "student_create": ['account.permissions.CurrentUserOrAdmin'],
            "words": ['perfection.permissions.StudentOrTeacherOrAdmin'],
            "words_create": ['perfection.permissions.TeacherOrAdmin'],
            "words_finish": ['perfection.permissions.Student']
        }
    ),
    "SERIALIZERS": ObjDict(
        {
            "word_perfection": 'perfection.serializers.words.WordPerfectionSerializer'
        }
    )
}
SETTINGS_TO_IMPORT = []


class Settings:
    def __init__(self, default_settings, explicit_overriden_settings: dict = None):
        if explicit_overriden_settings is None:
            explicit_overriden_settings = {}

        overriden_settings = (
                getattr(django_settings, PERFECTION_SETTINGS_NAMESPACE, {})
                or explicit_overriden_settings
        )

        self._load_default_settings()
        self._override_settings(overriden_settings)
        self._init_settings_to_import()

    def _load_default_settings(self):
        for setting_name, setting_value in default_settings.items():
            if setting_name.isupper():
                setattr(self, setting_name, setting_value)

    def _override_settings(self, overriden_settings: dict):
        for setting_name, setting_value in overriden_settings.items():
            value = setting_value
            if isinstance(setting_value, dict):
                value = getattr(self, setting_name, {})
                value.update(ObjDict(setting_value))
            setattr(self, setting_name, value)

    def _init_settings_to_import(self):
        for setting_name in SETTINGS_TO_IMPORT:
            value = getattr(self, setting_name)
            if isinstance(value, str):
                setattr(self, setting_name, import_string(value))


class LazySettings(LazyObject):
    def _setup(self, explicit_overriden_settings=None):
        self._wrapped = Settings(default_settings, explicit_overriden_settings)


settings = LazySettings()


def reload_djoser_settings(*args, **kwargs):
    global settings
    setting, value = kwargs["setting"], kwargs["value"]
    if setting == PERFECTION_SETTINGS_NAMESPACE:
        settings._setup(explicit_overriden_settings=value)


setting_changed.connect(reload_djoser_settings)