# -*- coding: utf-8 -*-
# ==============================================================================
#  Copyright (C) 2023 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2023-3-31 23:8                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : chIdioms.py                                                       =
#    @Program: website                                                         =
# ==============================================================================
import uuid
from typing import Optional

from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from perfection.utils.intervals import INTERVAL_UNACCEPTED_0, get_interval_count, get_next_interval
from utils import unique_random_str


class ChIdiomManager(models.Manager):
    pass


class ChIdiomLibrary(models.Model):
    class Meta:
        ordering = ['name']

    id = models.UUIDField(verbose_name="编号", primary_key=True, default=uuid.uuid4, editable=False, max_length=64)
    name = models.CharField(max_length=128, verbose_name='词库名称')
    is_default = models.BooleanField(verbose_name="是否为默认词库", default=True)


class ChIdiom(models.Model):
    """    """

    class Meta:
        ordering = ['random']

    key = models.CharField(max_length=40, verbose_name='成语')
    value = models.CharField(max_length=1000, verbose_name='解释')
    libraries = models.ManyToManyField(
        ChIdiomLibrary, max_length=128, verbose_name='所属词库', related_name='chIdioms'
    )

    random = models.CharField(max_length=24, primary_key=True, editable=False, unique=True, default=unique_random_str)
    objects = ChIdiomManager()


class ChIdiomsPerfectionManager(models.Manager):
    def create(self, rest=False, *args, **kwargs):
        perfection = kwargs.get('perfection')
        if perfection is None:
            raise ValueError('必须提供‘perfection’')
        # 生成随机单词
        total, addition_count = 5, 2
        if not rest:
            _next = timezone.now() + INTERVAL_UNACCEPTED_0[0]
            unremembered = perfection.chIdiom_perfections.filter(status=ChIdiomPerfectionStatusChoices.UNREMEMBERED)
            n = total - unremembered.count()
            remember = list(unremembered)
            excludes = perfection.chIdiom_perfections.all().values_list('chIdiom', flat=True)
            library = QuerySet(model=ChIdiom)
            for lib in perfection.chIdiom_libraries.all():
                library = library | lib.chIdioms.all()
            library = library.distinct()
            library = library.exclude(pk__in=list(excludes.values_list("chIdiom__pk", flat=True)))
            if n > 0:
                for item in library[:n]:
                    obj = ChIdiomPerfection.objects.create(
                        chIdiom=item, status=ChIdiomPerfectionStatusChoices.REMEMBERING
                    )
                    perfection.chIdiom_perfections.add(obj)
                    remember.append(obj)
            else:
                n = 0
            # 创建附加题，假设数据库变化不会影响qs
            addition = []
            for item in library[n:n + addition_count]:
                obj = ChIdiomPerfection.objects.create(chIdiom=item)
                perfection.chIdiom_perfections.add(obj)
                addition.append(obj)
        else:
            remember = []
            addition = []
        review = perfection.get_review_chIdioms()
        # print(remember, review)
        if len(remember) == 0 and len(review) == 0:
            return None
        chIdioms_perfection = super(ChIdiomsPerfectionManager, self).create(*args, **kwargs)
        chIdioms_perfection.review.add(*review)
        chIdioms_perfection.remember.add(*remember)
        chIdioms_perfection.addition.add(*addition)
        chIdioms_perfection.refresh_counts()
        chIdioms_perfection.save()
        perfection.save()
        return chIdioms_perfection


class ChIdiomPerfectionStatusChoices(models.TextChoices):
    UNREMEMBERED = "unremembered", "未记"
    REMEMBERING = "remembering", "正在记忆"
    REVIEWING = "reviewing", "正在复习"
    REMEMBERED = "remembered", "已记住"


class ChIdiomPerfection(models.Model):
    id = models.UUIDField(verbose_name="编号", primary_key=True, default=uuid.uuid4, editable=False, max_length=64)
    chIdiom = models.ForeignKey(
        'perfection.ChIdiom', related_name="chIdiom_perfection", verbose_name="单词信息", on_delete=models.CASCADE
    )
    status = models.TextField(
        max_length=64, choices=ChIdiomPerfectionStatusChoices.choices,
        default=ChIdiomPerfectionStatusChoices.UNREMEMBERED
    )

    unaccepted = models.PositiveIntegerField(default=0)  # 错误次数
    total = models.PositiveIntegerField(default=0)  # 总数
    count = models.PositiveIntegerField(default=0)  # 连续正确次数
    known = models.BooleanField(default=False)

    previous = models.DateField(auto_now_add=True, null=True)  # 上次复习时间
    next = models.DateField(default=None, null=True)  # 下次复习时间

    @property
    def need_to_review(self):
        return timezone.now().date() >= self.next


class ChIdiomsPerfectionStatusChoices(models.TextChoices):
    UNFINISHED = "unfinished", "未完成"
    FINISHED = "finished", "已完成"


class ChIdiomsPerfection(models.Model):
    class Meta:
        ordering = ['-updated']
        verbose_name = "成语打卡"
        verbose_name_plural = verbose_name

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, max_length=64)
    perfection = models.ForeignKey(
        'perfection.PerfectionStudent', related_name="chIdioms", on_delete=models.CASCADE
    )  # 单词打卡只能是学生
    remember = models.ManyToManyField(
        'perfection.ChIdiomPerfection', verbose_name="记忆单词", related_name="chIdioms_remember"
    )
    review = models.ManyToManyField(
        'perfection.ChIdiomPerfection', verbose_name="复习单词", related_name="chIdioms_review"
    )
    addition = models.ManyToManyField(
        'perfection.ChIdiomPerfection', verbose_name="附加题", related_name="chIdioms_addition"
    )
    unremembered = models.ManyToManyField(
        'perfection.ChIdiomPerfection', verbose_name="错误单词", related_name="chIdioms_unremembered"
    )
    picture = models.ManyToManyField('images.Image', verbose_name="打卡内容图片", related_name="chIdioms")

    # 在数据库中保存一部分东西，加快反应速度
    total = models.PositiveIntegerField(default=0)
    unaccepted = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(verbose_name="生成打卡任务时间", auto_now_add=True, editable=False)
    # 更新时间手动刷新，避免出错
    updated = models.DateTimeField(verbose_name="打卡任务更新时间", auto_now_add=True, editable=True)
    finished = models.DateTimeField(verbose_name="完成打卡任务时间", null=True)

    status = models.TextField(
        max_length=128, choices=ChIdiomsPerfectionStatusChoices.choices,
        default=ChIdiomsPerfectionStatusChoices.UNFINISHED
    )

    objects = ChIdiomsPerfectionManager()
    REQUIRED_FIELDS = ['perfection', ]
    SUMMARY_FIELDS = [
        'id', 'perfection',
        'created', 'updated', 'finished',
        'status', 'picture',
    ]

    # FINISH_REQUIRED_FIELDS = ['accepted', 'picture']
    # PUBLIC_FIELDS = ['perfection', 'remember', 'review']

    def update_chIdioms(self, review, addition):
        # 处理单词
        now = timezone.now()

        def update_chIdiom(chIdiom_, is_accepted, mode="review"):
            chIdiom_.previous = now
            chIdiom_.total += 1
            if is_accepted:
                chIdiom_.count += 1
                if chIdiom_.known or chIdiom_.count >= get_interval_count(chIdiom_):
                    chIdiom_.status = ChIdiomPerfectionStatusChoices.REMEMBERED
                else:
                    if mode == "review":
                        interval = get_next_interval(chIdiom_, 2)
                    elif mode == "addition":
                        chIdiom_.known = True
                        interval = get_next_interval(chIdiom_, 0)
                    else:
                        raise ValueError()
                    chIdiom_.next = now + interval
                    chIdiom_.status = ChIdiomPerfectionStatusChoices.REVIEWING
            else:
                chIdiom_.status = ChIdiomPerfectionStatusChoices.UNREMEMBERED
                chIdiom_.count = 0
                chIdiom_.known = False
                chIdiom_.unaccepted += 1
                if mode == "review":
                    self.unremembered.add(chIdiom_)
            chIdiom_.save()

        for item in self.review.all():
            update_chIdiom(item, review[item.chIdiom.key], mode="review")
        for item in self.addition.all():
            update_chIdiom(item, addition[item.chIdiom.key], mode="addition")
        self.unremembered.distinct()
        # 处理记忆版
        _next = now + get_next_interval(None, 1)
        for item in self.remember.all():
            item.next = _next
            item.status = ChIdiomPerfectionStatusChoices.REVIEWING
            item.save()
        self.save()

    @property
    def unremembered_chIdioms(self) -> QuerySet:
        return self.unremembered.all()

    def refresh_counts(self):
        self.total = self.get_total()
        self.unaccepted = self.get_unaccepted()
        # self.save()

    # @property
    def get_unaccepted(self) -> int:
        return self.unremembered_chIdioms.count()

    # @property
    def get_total(self) -> int:
        return self.review.count()

    @property
    def accuracy(self) -> Optional[float]:
        if self.status == ChIdiomsPerfectionStatusChoices.UNFINISHED:
            return None
        if self.total == 0:
            return 1
        return 1 - (self.unaccepted / self.total)

    @property
    def accuracy_str(self) -> Optional[str]:
        if self.status == ChIdiomsPerfectionStatusChoices.UNFINISHED:
            return None
        return '%.2f%%' % (self.accuracy * 100)

    # def get_picture_url(self):
    #     return settings.MEDIA_URL + str(self.picture)

    def __unicode__(self):
        return self.id
