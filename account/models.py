# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-12-2 21:27                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : models.py                                                         =
#    @Program: backend                                                         =
# ==============================================================================
import shortuuid
from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager, PermissionsMixin)
from djongo import models
from imagekit.models import ProcessedImageField
from pilkit.processors import ResizeToFill


class UserProfileManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        """
        创建用户
        """
        if not email:
            raise ValueError('用户必须拥有邮件地址')
        if not name:
            raise ValueError('用户必须拥有用户名')

        user = self.model(
            email=self.normalize_email(email),
            name=name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password):
        """
        创建并保存超级用户
        """
        user = self.create_user(
            email,
            password=password,
            name=name,
        )
        user.admin = 1
        user.save(using=self._db)
        return user


def _uuid(): return shortuuid.ShortUUID(alphabet="0123456789").random(8)


class AdminChoices(models.IntegerChoices):
    USER = 0, '普通用户'
    NORMAL = 1, '管理员'

    SUPER = 5, '超级管理员'
    DEVELOPER = 10, '开发者'


class User(AbstractBaseUser, PermissionsMixin, models.Model):
    # class Meta:
    #     ordering = ['created']

    email = models.EmailField(
        verbose_name='邮箱',
        max_length=255,
        unique=True,
    )
    uuid = models.CharField(verbose_name="用户id", primary_key=True, default=_uuid, editable=False, max_length=8)
    created = models.DateTimeField(verbose_name="创建时间", auto_now_add=True, editable=False)
    name = models.CharField(max_length=32, verbose_name="用户名", unique=True)
    signature = models.CharField(max_length=256, verbose_name="个性签名", default="")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    is_staff = models.BooleanField(default=False, verbose_name="是否为员工")
    admin = models.PositiveSmallIntegerField(
        choices=AdminChoices.choices, default=AdminChoices.USER, verbose_name="管理员级别"
    )
    avatar = ProcessedImageField(
        default='avatar/default.jpg', upload_to='avatar', verbose_name="头像",
        processors=[ResizeToFill(128, 128)], format='JPEG',
        options={'quality': 80}
    )

    objects = UserProfileManager()

    USERNAME_FIELD = 'name'
    REQUIRED_FIELDS = ['email']
    PUBLIC_FIELDS = ['uuid', 'name', 'avatar', 'signature', 'admin']
    PRIVATE_FIELDS = ['email', 'created', 'perfection']
    ALL_FIELDS = PUBLIC_FIELDS + PRIVATE_FIELDS

    def __str__(self):
        return self.name

    @property
    def perfection(self):
        if getattr(self, 'perfection_student', None):
            return self.perfection_student
        elif getattr(self, 'perfection_teacher', None):
            return self.perfection_teacher
        else:
            return None

    def get_avatar_url(self):
        return settings.MEDIA_URL + str(self.avatar)

    def get_full_name(self):
        # The user is identified by their email address
        return self.name

    def get_short_name(self):
        # The user is identified by their email address
        return self.name
