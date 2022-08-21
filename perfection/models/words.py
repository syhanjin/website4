# -*- coding: utf-8 -*-
# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-21 18:3                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : words.py                                                          =
#    @Program: website                                                         =
# ==============================================================================
import uuid
from datetime import timedelta

from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from perfection.conf import settings
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
    library = models.ForeignKey(
        WordLibrary, max_length=128, verbose_name='所属词库', related_name='words', on_delete=models.CASCADE
    )

    random = models.CharField(max_length=24, primary_key=True, editable=False, unique=True, default=unique_random_str)
    objects = WordManager()


class WordsPerfectionManager(models.Manager):
    def create(self, rest=False, *args, **kwargs):
        perfection = kwargs.get('perfection')
        if perfection is None:
            raise ValueError('必须提供‘perfection’')
        # 生成随机单词
        total = 20
        if not rest:
            unremembered = perfection.unremembered_words.all()
            # 首先保证保持词库
            remember = list(unremembered)
            if total > len(remember):
                # 补入未记词库的词
                reviewing = perfection.reviewing_words.all()
                remembered = perfection.remembered_words.all()
                excludes = list((remembered | reviewing | unremembered).values_list('word__pk', flat=True))
                library = QuerySet(model=Word)
                for lib in perfection.word_libraries.all():
                    library = library | lib.words.all()
                if len(excludes) == 0:
                    remember_unpack = library
                else:
                    remember_unpack = library.exclude(pk__in=excludes)
                # 包装
                for word in remember_unpack[:total - len(remember)]:
                    remember.append(WordPerfection.objects.create(word=word))
            review = perfection.get_review_words() + remember
        else:
            remember = []
            review = perfection.get_review_words()
        if len(remember) == 0 and len(review) == 0:
            return None
        words_perfection = super(WordsPerfectionManager, self).create(*args, **kwargs)
        words_perfection.review.add(*review)
        words_perfection.remember.add(*remember)
        words_perfection.save()
        return words_perfection


Ebbinghaus = [
    timedelta(days=1),
    timedelta(days=2),
    timedelta(days=4),
    timedelta(days=7),
    timedelta(days=15),
]


class WordPerfection(models.Model):
    id = models.UUIDField(verbose_name="编号", primary_key=True, default=uuid.uuid4, editable=False, max_length=64)
    word = models.ForeignKey(
        'perfection.Word', related_name="word_perfection", verbose_name="单词信息", on_delete=models.CASCADE
    )
    is_accepted = models.BooleanField(verbose_name="是否正确", null=True)
    remembered = models.DateField(verbose_name="记住它的时间", null=True)
    finished = models.DateField(verbose_name="复习完成时间", null=True)

    @property
    def need_to_review(self):
        if self.remembered is None:
            return False
        for t in Ebbinghaus:
            if (self.remembered + t) == timezone.now().date():
                return True
        return False

    @property
    def is_finished(self):
        return self.remembered is not None and (self.remembered + Ebbinghaus[-1]) <= timezone.now().date()


class WordsPerfection(models.Model):
    class Meta:
        ordering = ['-created']
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
    unremembered = models.ManyToManyField(
        'perfection.WordPerfection', verbose_name="错误单词", related_name="words_unremembered"
    )

    # accepted = models.PositiveIntegerField(verbose_name="正确数", default=0)
    # total = models.PositiveIntegerField(verbose_name="总数", default=0)
    # picture = models.ImageField(verbose_name="打卡内容图片", null=True, upload_to="perfection/words")
    picture = models.ManyToManyField('images.Image', verbose_name="打卡内容图片", related_name="words")

    created = models.DateTimeField(verbose_name="生成打卡任务时间", auto_now_add=True, editable=False)
    updated = models.DateTimeField(verbose_name="打卡任务更新时间", auto_now_add=True, editable=True)
    finished = models.DateTimeField(verbose_name="完成打卡任务时间", null=True)
    is_finished = models.BooleanField(verbose_name="是否已完成打卡", default=False)
    checked = models.DateTimeField(verbose_name="老师检查打卡时间", null=True)
    is_checked = models.BooleanField(verbose_name="是否检查打卡", default=False)
    rating = models.CharField(
        verbose_name="评级", max_length=16, choices=settings.CHOICES.rating_choice.choices, null=True
    )

    """
    后来发现这么设计不太合理，但是已经有数据了，要改需要处理数据库的问题
    以后改版去掉is_finished is_checked
    使用status判断状态(finished, checking, checked, rejected)
    """

    objects = WordsPerfectionManager()
    REQUIRED_FIELDS = ['perfection', ]
    SUMMARY_FIELDS = [
        'id', 'perfection', 'created',
        'picture', 'rating',
        'is_finished', 'finished',
        'is_checked', 'checked'
    ]

    # FINISH_REQUIRED_FIELDS = ['accepted', 'picture']
    # PUBLIC_FIELDS = ['perfection', 'remember', 'review']

    def update_words(self, review):
        # 处理单词
        for word in self.review.all():
            is_accepted = review[word.word.word]
            if is_accepted:
                if self.perfection.unremembered_words.filter(pk=word.pk).count() > 0:
                    # 若在保持词库则移除
                    self.perfection.unremembered_words.remove(word)
                if self.perfection.reviewing_words.filter(pk=word.pk).count() == 0:
                    # 不在复习词库，进入复习词库
                    word.remembered = timezone.now()
                    self.perfection.reviewing_words.add(word)
                elif word.is_finished:
                    # 复习单词，完成记忆，进入完成词库
                    self.perfection.reviewing_words.remove(word)
                    word.finished = timezone.now()
                    self.perfection.remembered_words.add(word)
            else:
                # 记录到自身
                if self.unremembered.filter(pk=word.pk).count() == 0:
                    self.unremembered.add(word)
                # 错误，进入保持词库
                if self.perfection.reviewing_words.filter(pk=word.pk).count() > 0:
                    # 若在复习词库则移除
                    self.perfection.reviewing_words.remove(word)
                    word.remembered = None
                if self.perfection.unremembered_words.filter(pk=word.pk).count() == 0:
                    self.perfection.unremembered_words.add(word)
            word.is_accepted = is_accepted
            word.save()
        self.perfection.save()
        self.save()

    @property
    def unremembered_words(self):
        return self.unremembered.all()

    @property
    def unaccepted(self) -> int:
        return self.unremembered.count()

    @property
    def total(self) -> int:
        return self.review.all().count()

    @property
    def accuracy(self):
        return 1 - (self.unaccepted / self.total) if self.is_finished else None

    @property
    def accuracy_str(self):
        return '%.2f%%' % (self.accuracy * 100) if self.is_finished else None

    # def get_picture_url(self):
    #     return settings.MEDIA_URL + str(self.picture)

    def __unicode__(self):
        return self.id
