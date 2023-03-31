# -*- coding: utf-8 -*-
# ==============================================================================
#  Copyright (C) 2023 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2023-3-31 23:8                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : words.py                                                          =
#    @Program: website                                                         =
# ==============================================================================
import uuid
from typing import Optional

from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from perfection.utils.intervals import INTERVAL_UNACCEPTED_0, get_interval_count, get_next_interval
from utils import unique_random_str


class WordManager(models.Manager):
    pass


class WordLibrary(models.Model):
    class Meta:
        ordering = ['name']

    id = models.UUIDField(verbose_name="编号", primary_key=True, default=uuid.uuid4, editable=False, max_length=64)
    name = models.CharField(max_length=128, verbose_name='词库名称')
    is_default = models.BooleanField(verbose_name="是否为默认词库", default=True)


class Word(models.Model):
    """
    说明：此为单词词库中的单词，chinese中包括词性和中文释义
    如：
    word: "focus"
    chinese: "v. （使）聚集 n. 焦点,中心,聚焦"
    """

    class Meta:
        ordering = ['random']

    word = models.CharField(max_length=40, verbose_name='英文')
    symbol = models.CharField(max_length=40, verbose_name='音标', null=True)
    chinese = models.CharField(max_length=1000, verbose_name='中文释义')
    libraries = models.ManyToManyField(
        WordLibrary, max_length=128, verbose_name='所属词库', related_name='words'
    )

    random = models.CharField(max_length=24, primary_key=True, editable=False, unique=True, default=unique_random_str)
    objects = WordManager()


class WordsPerfectionManager(models.Manager):
    def create(self, rest=False, *args, **kwargs):
        perfection = kwargs.get('perfection')
        if perfection is None:
            raise ValueError('必须提供‘perfection’')
        # 生成随机单词
        total, addition_count = 30, 10
        if not rest:
            _next = timezone.now() + INTERVAL_UNACCEPTED_0[0]
            unremembered = perfection.word_perfections.filter(status=WordPerfectionStatusChoices.UNREMEMBERED)
            n = total - unremembered.count()
            remember = list(unremembered)
            excludes = perfection.word_perfections.all().values_list('word', flat=True)
            library = QuerySet(model=Word)
            for lib in perfection.word_libraries.all():
                library = library | lib.words.all()
            library = library.distinct()
            library = library.exclude(pk__in=list(excludes.values_list("word__pk", flat=True)))
            if n > 0:
                for word in library[:n]:
                    obj = WordPerfection.objects.create(
                        word=word, status=WordPerfectionStatusChoices.REMEMBERING
                    )
                    perfection.word_perfections.add(obj)
                    remember.append(obj)
            else:
                n = 0
            # 创建附加题，假设数据库变化不会影响qs
            addition = []
            for word in library[n:n + addition_count]:
                obj = WordPerfection.objects.create(word=word)
                perfection.word_perfections.add(obj)
                addition.append(obj)
        else:
            remember = []
            addition = []
        review = perfection.get_review_words()
        # print(remember, review)
        if len(remember) == 0 and len(review) == 0:
            return None
        words_perfection = super(WordsPerfectionManager, self).create(*args, **kwargs)
        words_perfection.review.add(*review)
        words_perfection.remember.add(*remember)
        words_perfection.addition.add(*addition)
        words_perfection.refresh_counts()
        words_perfection.save()
        perfection.save()
        return words_perfection


class WordPerfectionStatusChoices(models.TextChoices):
    UNREMEMBERED = "unremembered", "未记"
    REMEMBERING = "remembering", "正在记忆"
    REVIEWING = "reviewing", "正在复习"
    REMEMBERED = "remembered", "已记住"


class WordPerfection(models.Model):
    id = models.UUIDField(verbose_name="编号", primary_key=True, default=uuid.uuid4, editable=False, max_length=64)
    word = models.ForeignKey(
        'perfection.Word', related_name="word_perfection", verbose_name="单词信息", on_delete=models.CASCADE
    )
    status = models.TextField(
        max_length=64, choices=WordPerfectionStatusChoices.choices, default=WordPerfectionStatusChoices.UNREMEMBERED
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


class WordsPerfectionStatusChoices(models.TextChoices):
    UNFINISHED = "unfinished", "未完成"
    FINISHED = "finished", "已完成"


class WordsPerfection(models.Model):
    class Meta:
        ordering = ['-updated']
        verbose_name = "单词打卡"
        verbose_name_plural = verbose_name

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, max_length=64)
    perfection = models.ForeignKey(
        'perfection.PerfectionStudent', related_name="words", on_delete=models.CASCADE
    )  # 单词打卡只能是学生
    remember = models.ManyToManyField(
        'perfection.WordPerfection', verbose_name="记忆单词", related_name="words_remember"
    )
    review = models.ManyToManyField(
        'perfection.WordPerfection', verbose_name="复习单词", related_name="words_review"
    )
    addition = models.ManyToManyField(
        'perfection.WordPerfection', verbose_name="附加题", related_name="words_addition"
    )
    unremembered = models.ManyToManyField(
        'perfection.WordPerfection', verbose_name="错误单词", related_name="words_unremembered"
    )
    picture = models.ManyToManyField('images.Image', verbose_name="打卡内容图片", related_name="words")

    # accepted = models.FloatField(default=0)
    # 在数据库中保存一部分东西，加快反应速度
    total = models.PositiveIntegerField(default=0)
    unaccepted = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(verbose_name="生成打卡任务时间", auto_now_add=True, editable=False)
    # 更新时间手动刷新，避免出错
    updated = models.DateTimeField(verbose_name="打卡任务更新时间", auto_now_add=True, editable=True)
    finished = models.DateTimeField(verbose_name="完成打卡任务时间", null=True)

    status = models.TextField(
        max_length=128, choices=WordsPerfectionStatusChoices.choices, default=WordsPerfectionStatusChoices.UNFINISHED
    )

    objects = WordsPerfectionManager()
    REQUIRED_FIELDS = ['perfection', ]
    SUMMARY_FIELDS = [
        'id', 'perfection',
        'created', 'updated', 'finished',
        'status', 'picture',
    ]

    # FINISH_REQUIRED_FIELDS = ['accepted', 'picture']
    # PUBLIC_FIELDS = ['perfection', 'remember', 'review']

    def update_words(self, review, addition):
        # 处理单词
        now = timezone.now()

        def update_word(word_, is_accepted, mode="review"):
            word_.previous = now
            word_.total += 1
            if is_accepted:
                word_.count += 1
                if word_.known or word_.count >= get_interval_count(word_):
                    word_.status = WordPerfectionStatusChoices.REMEMBERED
                else:
                    if mode == "review":
                        interval = get_next_interval(word_, 2)
                    elif mode == "addition":
                        word.known = True
                        interval = get_next_interval(word_, 0)
                    else:
                        raise ValueError()
                    word_.next = now + interval
                    word_.status = WordPerfectionStatusChoices.REVIEWING
            else:
                word_.status = WordPerfectionStatusChoices.UNREMEMBERED
                word_.count = 0
                word_.known = False
                word_.unaccepted += 1
                if mode == "review":
                    self.unremembered.add(word_)
            word_.save()

        for word in self.review.all():
            update_word(word, review[word.word.word], mode="review")
        for word in self.addition.all():
            update_word(word, addition[word.word.word], mode="addition")
        self.unremembered.distinct()
        # 处理记忆版
        _next = now + get_next_interval(None, 1)
        for item in self.remember.all():
            item.next = _next
            item.status = WordPerfectionStatusChoices.REVIEWING
            item.save()
        self.save()

    @property
    def unremembered_words(self) -> QuerySet:
        return self.unremembered.all()

    def refresh_counts(self):
        self.total = self.get_total()
        self.unaccepted = self.get_unaccepted()
        # self.save()

    # @property
    def get_unaccepted(self) -> int:
        return self.unremembered_words.count()

    # @property
    def get_total(self) -> int:
        return self.review.count()

    @property
    def accuracy(self) -> Optional[float]:
        if self.status == WordsPerfectionStatusChoices.UNFINISHED:
            return None
        if self.total == 0:
            return 1
        return 1 - (self.unaccepted / self.total)

    @property
    def accuracy_str(self) -> Optional[str]:
        if self.status == WordsPerfectionStatusChoices.UNFINISHED:
            return None
        return '%.2f%%' % (self.accuracy * 100)

    # def get_picture_url(self):
    #     return settings.MEDIA_URL + str(self.picture)

    def __unicode__(self):
        return self.id
