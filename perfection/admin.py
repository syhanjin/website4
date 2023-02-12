# ==============================================================================
#  Copyright (C) 2023 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2023-2-10 23:35                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : admin.py                                                          =
#    @Program: website                                                         =
# ==============================================================================
import json
from datetime import time, timedelta

import pandas as pd
from django.utils import timezone

from getui.models import NotificationMessageOffline, NotificationMessageOnline
from getui.servers.push import to_single_batch_alias
from perfection.conf import settings
from perfection.models.base import PerfectionStudent
from perfection.models.chIdioms import ChIdiom, ChIdiomLibrary, ChIdiomsPerfection
from perfection.models.chWords import ChWord, ChWordLibrary, ChWordsPerfection
from perfection.models.words import WordsPerfection

DELTA = timedelta(minutes=5)

MIM_CHECK_TIME = time(hour=5, minute=55)
MAX_CHECK_TIME = time(hour=22, minute=59)
TIME_RANGE = (
    time(hour=5, minute=55),
    time(hour=22, minute=35),
)

REMIND_TIMES = [
    # 由于华为推送限制，暂时关闭大部分推送 2022-09-21
    # time(hour=18, minute=00),
    # time(hour=20, minute=00),
    # time(hour=21, minute=30),
    time(hour=22, minute=00),
    # time(hour=22, minute=30)
]


def _is_remind(t):
    for _time in REMIND_TIMES:
        if (t - DELTA).time() <= _time <= (t + DELTA).time():
            return True
    return False


def _payload(wp):
    return json.dumps(
        {
            "action": "open_page",
            "url": f'/pages/perfection/words/words?wp_id={wp.id}'
        }
    )


def _create_remind(data, alias, group_name):
    return {
        "push": NotificationMessageOnline.objects.create(
            **data,
            channel_id="Push",
            channel_name="Push",
            channel_level=4
        ),
        "channel": NotificationMessageOffline.objects.create(**data),
        "group_name": group_name,
        "alias": alias
    }


def create_words_perfection(is_rest, perfection, date_str):
    wp = WordsPerfection.objects.create(rest=is_rest, perfection=perfection)
    if wp is None:
        return None
    # 构建推送信息
    rem_cnt, rev_cnt = wp.remember.count(), wp.review.count()
    data = {
        "title": "今日的单词打卡内容已下发，请尽快完成",
        "body": f"共{rem_cnt}个新单词，{rev_cnt}个复习单词",
        "big_text": (f"共{rem_cnt}个新单词，{rev_cnt}个复习单词\n"
                     + ("今天休息，没有新单词，但是该复习的还是得复习哦\n" if is_rest else "")
                     + f"今天也要记得按时完成打卡任务哦~~"),
        "click_type": "intent",
        "payload": _payload(wp)
    }
    return _create_remind(data, perfection.user.uuid, date_str + "_new")


def create_words_perfections():
    now = timezone.now()
    if not (TIME_RANGE[0] <= now.time() <= TIME_RANGE[1]):
        return
    is_rest, is_remind = now.weekday() == 6, _is_remind(now)
    is_rest = False
    date_str = now.__format__('%Y-%m-%d')
    reminds = []
    add_cnt, upd_cnt = 0, 0
    for perfection in PerfectionStudent.objects.all():
        # print(perfection)
        # 首先获取最后一次打卡
        latest = perfection.get_latest(perfection.words)
        if not latest or latest.status == settings.CHOICES.words_perfection_status.FINISHED:
            res = create_words_perfection(is_rest, perfection, date_str)
            if res is None:
                continue
            reminds.append(res)
            add_cnt += 1
        elif latest.status == settings.CHOICES.words_perfection_status.UNFINISHED and latest.updated.date() < now.date():
            review = list(latest.review.all())
            review_new = perfection.get_review_words()
            for word in review_new:
                if word not in review:
                    latest.review.add(word)
            latest.updated = now
            latest.save()
            # 构建推送信息
            rem_cnt, rev_cnt = latest.remember.count(), latest.review.count()
            data = {
                "title": "漏打单词内容已更新，请尽快完成",
                "body": f"共{rem_cnt}个新单词，{rev_cnt}个复习单词\n",
                "big_text": f"共{rem_cnt}个新单词，{rev_cnt}个复习单词\n"
                            f"你已经拖欠打卡{(now.date() - latest.created.date()).days}天了\n"
                            f"当天的任务要当天完成，这么拖合适吗？",
                "click_type": "intent",
                "payload": _payload(latest)
            }
            reminds.append(_create_remind(data, perfection.user.uuid, date_str + "_upd"))
            upd_cnt += 1
        elif is_remind and not latest.is_finished:
            data = {
                "title": "今日单词打卡任务未完成",
                "body": "催打卡啦，催打卡啦，今日的打卡任务还没完成",
                "big_text": ("催打卡啦，催打卡啦，今日的打卡任务还没完成\n"
                             + ("今天休息，没有新单词，但是该复习的还是得复习，" if is_rest else "")
                             + "不要把今天的任务推到明天哦"),
                "click_type": "intent",
                "payload": _payload(latest)
            }
            reminds.append(_create_remind(data, perfection.user.uuid, date_str + "_rmd"))
    if len(reminds) == 0:
        return
    print(' =' * 10)
    print(
        f"{now.__format__('%Y-%m-%d %H:%M:%S')}处理单词打卡内容\n"
        f"共{add_cnt}个新发布，{upd_cnt}个漏打更新，{len(reminds)}条提醒内容"
    )
    for remind_batch in range(0, len(reminds), 200):
        is_success, msg = to_single_batch_alias(reminds[remind_batch: remind_batch + 200])
        print(f"发布提醒：{is_success}, {msg}")


def create_chIdioms_perfections():
    now = timezone.now()
    if not (TIME_RANGE[0] <= now.time() <= TIME_RANGE[1]):
        return
    is_rest, is_remind = now.weekday() == 6, _is_remind(now)
    is_rest = False
    date_str = now.__format__('%Y-%m-%d')
    reminds = []
    add_cnt, upd_cnt = 0, 0
    for perfection in PerfectionStudent.objects.all():
        # print(perfection)
        # 首先获取最后一次打卡
        latest = perfection.get_latest(perfection.chIdioms)
        if not latest or latest.status == settings.CHOICES.chIdioms_perfection_status.FINISHED:
            ChIdiomsPerfection.objects.create(rest=is_rest, perfection=perfection)
            add_cnt += 1
        elif latest.status == settings.CHOICES.chIdioms_perfection_status.UNFINISHED and latest.updated.date() < now.date():
            review = list(latest.review.all())
            review_new = perfection.get_review_chIdioms()
            for item in review_new:
                if item not in review:
                    latest.review.add(item)
            latest.updated = now
            latest.save()
            upd_cnt += 1
        elif is_remind and not latest.is_finished:
            pass
    if upd_cnt + add_cnt == 0:
        return
    print(' =' * 10)
    print(
        f"{now.__format__('%Y-%m-%d %H:%M:%S')}处理成语打卡内容\n"
        f"共{add_cnt}个新发布，{upd_cnt}个漏打更新"
    )


def load_chIdiom_list(path):
    """
    导入成语列表 手动输入词库，出现重复成语将被覆盖
    :param path: 文件(excel)
    :return: 导入数量, 总数
    """
    library_name = input('library: ')
    if not library_name:
        return
    library, created = ChIdiomLibrary.objects.update_or_create(defaults={"name": library_name}, name=library_name)
    if created:
        print(f"已新建词库{library_name}")
    is_default = input(f'是否设置词库{library_name}为默认词库(Y/n): ')
    if is_default == '' or is_default.lower() == 'y':
        is_default = True
    elif is_default.lower() == 'n':
        is_default = False
    else:
        raise ValueError('输入错误')
    library.is_default = is_default
    library.save()
    chIdiom_list = pd.read_excel(path)
    columns = chIdiom_list.columns.values.tolist()
    print(
        f"正在导入{chIdiom_list.shape[0]}个单词进入词库[{library.name}]，\n"
        # f"注意：之前已经导入过得单词将从原词库移除并编入该词库，之前的词义将被覆盖"
    )
    if not {'成语', '解释'} <= set(columns):
        raise ValueError('成语列表文件需包含 “成语” “解释” 两列')
    for idx, row in chIdiom_list.iterrows():
        _key = row['成语'].replace(' ', "")
        _value = row['解释'].strip()
        chIdiom = ChIdiom.objects.filter(key=_key)
        if not chIdiom.exists():
            chIdiom = ChIdiom.objects.create(key=_key, value=_value)
            chIdiom.libraries.add(library)
            chIdiom.save()
        else:
            chIdiom = chIdiom.first()
            if not chIdiom.libraries.filter(pk=library.pk).exists():
                chIdiom.libraries.add(library)
            if chIdiom.value != _value:
                op = input(f"{_key}: (1 {_value} <==> (2[Default] {chIdiom.value} ==> (3 手动输入 :")
                if op == "1":
                    chIdiom.value = _value
                elif op == "2":
                    pass
                elif op == "3":
                    _value = input(f"输入词义({_key}): ")
                    chIdiom.value = _value
            chIdiom.save()
    print(
        f"导入完成！\n"
        f"现总词数：{ChIdiom.objects.count()}\n"
        f"全部词库：{list(ChIdiomLibrary.objects.all().values_list('name', flat=True))}"
    )
    return chIdiom_list.shape[0], ChIdiom.objects.count()


def create_chWords_perfections():
    now = timezone.now()
    if not (TIME_RANGE[0] <= now.time() <= TIME_RANGE[1]):
        return
    is_rest, is_remind = now.weekday() == 6, _is_remind(now)
    is_rest = False
    add_cnt, upd_cnt = 0, 0
    for perfection in PerfectionStudent.objects.all():
        # print(perfection)
        # 首先获取最后一次打卡
        latest = perfection.get_latest(perfection.chWords)
        if not latest or latest.status == settings.CHOICES.chWords_perfection_status.FINISHED:
            ChWordsPerfection.objects.create(rest=is_rest, perfection=perfection)
            add_cnt += 1
        elif latest.status == settings.CHOICES.chWords_perfection_status.UNFINISHED and latest.updated.date() < now.date():
            review = list(latest.review.all())
            review_new = perfection.get_review_chWords()
            for item in review_new:
                if item not in review:
                    latest.review.add(item)
            latest.updated = now
            latest.save()
            upd_cnt += 1
        elif is_remind and not latest.is_finished:
            pass
    if upd_cnt + add_cnt == 0:
        return
    print(' =' * 10)
    print(
        f"{now.__format__('%Y-%m-%d %H:%M:%S')}处理成语打卡内容\n"
        f"共{add_cnt}个新发布，{upd_cnt}个漏打更新"
    )


def load_chWord_list(path):
    """
    导入成语列表 手动输入词库，出现重复成语将被覆盖
    :param path: 文件(excel)
    :return: 导入数量, 总数
    """
    library_name = input('library: ')
    if not library_name:
        return
    library, created = ChWordLibrary.objects.update_or_create(defaults={"name": library_name}, name=library_name)
    if created:
        print(f"已新建词库{library_name}")
    is_default = input(f'是否设置词库{library_name}为默认词库(Y/n): ')
    if is_default == '' or is_default.lower() == 'y':
        is_default = True
    elif is_default.lower() == 'n':
        is_default = False
    else:
        raise ValueError('输入错误')
    library.is_default = is_default
    library.save()
    chWord_list = pd.read_excel(path)
    columns = chWord_list.columns.values.tolist()
    print(
        f"正在导入{chWord_list.shape[0]}个单词进入词库[{library.name}]，\n"
        # f"注意：之前已经导入过得单词将从原词库移除并编入该词库，之前的词义将被覆盖"
    )
    if not {'字词', '例句', '意思'} <= set(columns):
        raise ValueError('单词列表文件需包含 “字词” “例句” “意思” 三列')
    for idx, row in chWord_list.iterrows():
        _key = row['字词'].replace(' ', "")
        _sentence = row['例句'].strip()
        _value = row['意思'].strip()
        chWord = ChWord.objects.filter(key=_key, value=_value)
        if not chWord.exists():
            chWord = ChWord.objects.create(key=_key, sentence=_sentence, value=_value)
            chWord.libraries.add(library)
            chWord.save()
        else:
            chWord = chWord.first()
            if not chWord.libraries.filter(pk=library.pk).exists():
                chWord.libraries.add(library)
            if chWord.value != _value:
                op = input(f"{_key}[{_value}]: (1 {_sentence} <==> (2[Default] {chWord.sentence} ==> (3 手动输入 :")
                if op == "1":
                    chWord.sentence = _sentence
                elif op == "2":
                    pass
                elif op == "3":
                    _value = input(f"输入例句({_key}[{_value}]): ")
                    chWord.sentence = _sentence
            chWord.save()
    print(
        f"导入完成！\n"
        f"现总词数：{ChWord.objects.count()}\n"
        f"全部词库：{list(ChWordLibrary.objects.all().values_list('name', flat=True))}"
    )
    return chWord_list.shape[0], ChWord.objects.count()
