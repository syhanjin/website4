# -*- coding: utf-8 -*-
# ==============================================================================
#  Copyright (C) 2023 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2023-2-8 22:43                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : chWords.py                                                        =
#    @Program: website                                                         =
# ==============================================================================
import uuid
from typing import Optional

from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from perfection.utils.intervals import INTERVAL_UNACCEPTED_0, get_interval_count, get_next_interval
from utils import unique_random_str


class ChWordManager(models.Manager):
    pass


class ChWordLibrary(models.Model):
    class Meta:
        ordering = ['name']

    id = models.UUIDField(verbose_name="编号", primary_key=True, default=uuid.uuid4, editable=False, max_length=64)
    name = models.CharField(max_length=128, verbose_name='词库名称')
    is_default = models.BooleanField(verbose_name="是否为默认词库", default=True)


class ChWord(models.Model):
    """    """

    class Meta:
        ordering = ['random']

    key = models.CharField(max_length=40, verbose_name='字')
    sentence = models.CharField(max_length=128, verbose_name='例句')
    value = models.CharField(max_length=1000, verbose_name='解释')
    libraries = models.ManyToManyField(
        ChWordLibrary, max_length=128, verbose_name='所属词库', related_name='chWords'
    )

    random = models.CharField(max_length=24, primary_key=True, editable=False, unique=True, default=unique_random_str)
    objects = ChWordManager()


class ChWordsPerfectionManager(models.Manager):
    def create(self, rest=False, *args, **kwargs):
        perfection = kwargs.get('perfection')
        if perfection is None:
            raise ValueError('必须提供‘perfection’')
        # 生成随机单词
        total, addition_count = 20, 10
        if not rest:
            _next = timezone.now() + INTERVAL_UNACCEPTED_0[0]
            unremembered = perfection.chWord_perfections.filter(status=ChWordPerfectionStatusChoices.UNREMEMBERED)
            n = total - unremembered.count()
            remember = []
            for item in unremembered:
                # 重置下次打卡时间
                item.next = _next
                item.save()
                remember.append(item)
            excludes = perfection.chWord_perfections.all().values_list('chWord', flat=True)
            library = QuerySet(model=ChWord)
            for lib in perfection.chWord_libraries.all():
                library = library | lib.chWords.all()
            library = library.distinct()
            library = library.exclude(pk__in=list(excludes.values_list("chWord__pk", flat=True)))
            if n > 0:
                for item in library[:n]:
                    obj = ChWordPerfection.objects.create(
                        chWord=item, status=ChWordPerfectionStatusChoices.REVIEWING, next=_next
                    )
                    perfection.chWord_perfections.add(obj)
                    remember.append(obj)
            else:
                n = 0
            # 创建附加题，假设数据库变化不会影响qs
            addition = []
            for item in library[n:n + addition_count]:
                obj = ChWordPerfection.objects.create(chWord=item)
                perfection.chWord_perfections.add(obj)
                addition.append(obj)
        else:
            remember = []
            addition = []
        review = perfection.get_review_chWords()
        # print(remember, review)
        if len(remember) == 0 and len(review) == 0:
            return None
        chWords_perfection = super(ChWordsPerfectionManager, self).create(*args, **kwargs)
        chWords_perfection.review.add(*review)
        chWords_perfection.remember.add(*remember)
        chWords_perfection.addition.add(*addition)
        chWords_perfection.save()
        perfection.save()
        return chWords_perfection


class ChWordPerfectionStatusChoices(models.TextChoices):
    UNREMEMBERED = "unremembered", "未记"
    REMEMBERING = "remembering", "正在记忆"
    REVIEWING = "reviewing", "正在复习"
    REMEMBERED = "remembered", "已记住"


class ChWordPerfection(models.Model):
    id = models.UUIDField(verbose_name="编号", primary_key=True, default=uuid.uuid4, editable=False, max_length=64)
    chWord = models.ForeignKey(
        'perfection.ChWord', related_name="chWord_perfection", verbose_name="单词信息", on_delete=models.CASCADE
    )
    status = models.TextField(
        max_length=64, choices=ChWordPerfectionStatusChoices.choices,
        default=ChWordPerfectionStatusChoices.UNREMEMBERED
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


class ChWordsPerfectionStatusChoices(models.TextChoices):
    UNFINISHED = "unfinished", "未完成"
    FINISHED = "finished", "已完成"


class ChWordsPerfection(models.Model):
    class Meta:
        ordering = ['-updated']
        verbose_name = "成语打卡"
        verbose_name_plural = verbose_name

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, max_length=64)
    perfection = models.ForeignKey(
        'perfection.PerfectionStudent', related_name="chWords", on_delete=models.CASCADE
    )  # 单词打卡只能是学生
    remember = models.ManyToManyField(
        'perfection.ChWordPerfection', verbose_name="记忆单词", related_name="chWords_remember"
    )
    review = models.ManyToManyField(
        'perfection.ChWordPerfection', verbose_name="复习单词", related_name="chWords_review"
    )
    addition = models.ManyToManyField(
        'perfection.ChWordPerfection', verbose_name="附加题", related_name="chWords_addition"
    )
    unremembered = models.ManyToManyField(
        'perfection.ChWordPerfection', verbose_name="错误单词", related_name="chWords_unremembered"
    )
    picture = models.ManyToManyField('images.Image', verbose_name="打卡内容图片", related_name="chWords")

    # accepted = models.FloatField(default=0)

    created = models.DateTimeField(verbose_name="生成打卡任务时间", auto_now_add=True, editable=False)
    updated = models.DateTimeField(verbose_name="打卡任务更新时间", auto_now=True, editable=True)
    finished = models.DateTimeField(verbose_name="完成打卡任务时间", null=True)

    status = models.TextField(
        max_length=128, choices=ChWordsPerfectionStatusChoices.choices,
        default=ChWordsPerfectionStatusChoices.UNFINISHED
    )

    objects = ChWordsPerfectionManager()
    REQUIRED_FIELDS = ['perfection', ]
    SUMMARY_FIELDS = [
        'id', 'perfection',
        'created', 'updated', 'finished',
        'status', 'picture',
    ]

    # FINISH_REQUIRED_FIELDS = ['accepted', 'picture']
    # PUBLIC_FIELDS = ['perfection', 'remember', 'review']

    def update_chWords(self, review, addition):
        # 处理单词
        def update_chWord(chWord_, is_accepted, mode="review"):
            chWord_.previous = now
            chWord_.total += 1
            if is_accepted:
                chWord_.count += 1
                if chWord_.known or chWord_.count >= get_interval_count(chWord_):
                    chWord_.status = ChWordPerfectionStatusChoices.REMEMBERED
                else:
                    if mode == "review":
                        interval = get_next_interval(chWord_, 2)
                    elif mode == "addition":
                        chWord_.known = True
                        interval = get_next_interval(chWord_, 0)
                    else:
                        raise ValueError()
                    chWord_.next = now + interval
                    chWord_.status = ChWordPerfectionStatusChoices.REVIEWING
            else:
                chWord_.status = ChWordPerfectionStatusChoices.UNREMEMBERED
                chWord_.count = 0
                chWord_.known = False
                chWord_.unaccepted += 1
                if mode == "review":
                    self.unremembered.add(chWord_)
            chWord_.save()

        now = timezone.now()
        for item in self.review.all():
            update_chWord(item, review[item.chWord.key], mode="review")
        for item in self.addition.all():
            update_chWord(item, addition[item.chWord.key], mode="addition")
        self.unremembered.distinct()
        self.save()

    @property
    def unremembered_chWords(self) -> QuerySet:
        return self.unremembered.all()

    @property
    def unaccepted(self) -> int:
        return self.unremembered_chWords.count()

    @property
    def total(self) -> int:
        return self.review.count()

    @property
    def accuracy(self) -> Optional[float]:
        if self.status == ChWordsPerfectionStatusChoices.UNFINISHED:
            return None
        if self.total == 0:
            return 1
        return 1 - (self.unaccepted / self.total)

    @property
    def accuracy_str(self) -> Optional[str]:
        if self.status == ChWordsPerfectionStatusChoices.UNFINISHED:
            return None
        return '%.2f%%' % (self.accuracy * 100)

    # def get_picture_url(self):
    #     return settings.MEDIA_URL + str(self.picture)

    def __unicode__(self):
        return self.id
