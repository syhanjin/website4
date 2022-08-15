# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-15 11:53                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : models.py                                                         =
#    @Program: website                                                         =
# ==============================================================================
import uuid

from django.db import models


class ImageManager(models.Manager):
    pass


class Image(models.Model):
    class Meta:
        ordering = ['-created']

    image = models.ImageField(upload_to="images")
    id = models.UUIDField(verbose_name="编号", primary_key=True, default=uuid.uuid4, editable=False, max_length=64)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    objects = ImageManager()

    def __unicode__(self):
        return str(self.created)

    @property
    def url(self):
        return self.image.url
