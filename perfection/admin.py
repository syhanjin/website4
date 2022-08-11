# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-11 20:12                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : admin.py                                                          =
#    @Program: website                                                         =
# ==============================================================================
import json
from datetime import time, timedelta

import pandas as pd
from django.utils import timezone

from getui.models import NotificationMessageOnline
from getui.servers.push import to_single_batch_alias
from perfection.models.base import PerfectionStudent
from perfection.models.words import Word, WordLibrary, WordsPerfection

DELTA = timedelta(minutes=5)

MIM_CHECK_TIME = time(hour=6)
MAX_CHECK_TIME = time(hour=22, minute=30)

REMIND_TIMES = [
    time(hour=18, minute=00),
    time(hour=20, minute=00),
    time(hour=21, minute=30),
    time(hour=22, minute=00),
    time(hour=22, minute=30)
]


def create_words_perfections():
    """
    自动检查，未创建单词打卡的同学自动创建
    :return:
    """
    # 扫描所有打卡学生，选出今天有没有打卡任务且所有任务已完成的人
    # perfections = PerfectionStudent.objects.filter(can_add_words_perfection=True)
    # 判断时间，是否需要处理，只判断小时
    now = timezone.now()
    if not (MIM_CHECK_TIME <= now.time() <= MAX_CHECK_TIME):
        return
    # 逐个发布打卡
    log = [' =' * 10]
    rest, remind = False, False
    log.append(f'检查并发布打卡-{now.__format__("%Y-%m-%d %H:%M:%S")}')
    if now.weekday() == 6:
        log.append("今日为星期日，发布的打卡中将不会有新记单词")
        rest = True
    for tm in REMIND_TIMES:
        if (now - DELTA).time() <= tm <= (now + DELTA).time():
            log.append("**提醒打卡**")
            remind = True
            break

    reminds = []
    date_str = now.__format__("%Y-%m-%d")
    add_cnt, miss_cnt = 0, 0
    for perfection in PerfectionStudent.objects.all():
        if perfection.can_add_words_perfection:
            wp = WordsPerfection.objects.create(
                user=perfection.user,
                rest=rest
            )
            # 构建推送信息
            notification = NotificationMessageOnline.objects.create(
                title="今日的单词打卡内容已下发，请查收",
                body=f"共{wp.remember.count()}个新单词，{wp.review.count()}个复习单词",
                big_text=(f"共{wp.remember.count()}个新单词，{wp.review.count()}个复习单词\n"
                          + ("今天休息，没有新单词，但是该复习的还是得复习哦\n" if rest else "")
                          + f"今天也要记得按时打卡哦~~"),
                click_type="intent",
                payload=json.dumps(
                    {
                        "action": "open_page",
                        "url": f'/pages/perfection/words/words?wp_id={wp.id}'
                    }
                )
            )
            reminds.append(
                {
                    "push": notification,
                    "group_name": date_str + "_new",
                    "alias": perfection.user.uuid
                }
            )
            add_cnt += 1
        elif perfection.can_update_words_perfection:
            # 扫描漏打的人并更新打卡内容
            latest = perfection.get_latest(perfection.words)
            review = list(latest.review.all())
            review_new = perfection.get_review_words()
            for word in review_new:
                if word not in review:
                    latest.review.add(word)
            latest.updated = timezone.now()
            latest.save()
            # 构建推送信息
            notification = NotificationMessageOnline.objects.create(
                title="您之间漏打的单词打卡已更新",
                body=f"共{latest.remember.count()}个新单词，{latest.review.count()}个复习单词\n",
                big_text=f"共{latest.remember.count()}个新单词，{latest.review.count()}个复习单词\n"
                         f"明日复明日，明日何其多，不如今天就完成吧",
                click_type="intent",
                payload=json.dumps(
                    {
                        "action": "open_page",
                        "url": f'/pages/perfection/words/words?wp_id={latest.id}'
                    }
                ),
                channel_level=4
            )
            reminds.append(
                {
                    "push": notification,
                    "group_name": date_str + "_update",
                    "alias": perfection.user.uuid
                }
            )
            miss_cnt += 1
        elif remind and perfection.has_unfinished_words_perfection:
            latest = perfection.get_latest(perfection.words)
            # 构建推送信息
            notification = NotificationMessageOnline.objects.create(
                title="今日单词打卡任务未完成",
                body="",
                big_text=("催打卡啦，催打卡啦，赶快打完卡避免夜长梦多！\n"
                          + ("今天休息，没有新单词，但是该复习的还是得复习，" if rest else "")
                          + "不要把打卡任务推到明天哦"),
                click_type="intent",
                payload=json.dumps(
                    {
                        "action": "open_page",
                        "url": f'/pages/perfection/words/words?wp_id={latest.id}'
                    }
                ),
                channel_level=4
            )
            reminds.append(
                {
                    "push": notification,
                    "group_name": date_str + "_urge",
                    "alias": perfection.user.uuid
                }
            )
    for remind_batch in range(0, len(reminds), 200):
        is_success, msg = to_single_batch_alias(reminds[remind_batch: remind_batch + 200])
        log.append(f'{is_success}, {msg}')
    log.append(f'发布完毕！共{add_cnt}个新发布，{miss_cnt}个漏打更新，{len(reminds)}条提醒内容')
    if add_cnt + miss_cnt + len(reminds) > 0:
        for i in log:
            print(i)


def load_word_list(path):
    """
    导入单词列表 手动输入词库，出现重复单词将被覆盖
    :param path: 文件(excel)
    :return: 导入数量, 总数
    """
    library_name = input('library: ')
    if not library_name:
        return
    library, created = WordLibrary.objects.update_or_create(defaults={"name": library_name}, name=library_name)
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
    word_list = pd.read_excel(path)
    columns = word_list.columns.values.tolist()
    print(
        f"正在导入{word_list.shape[0]}个单词进入词库[{library.name}]，\n"
        f"注意：之前已经导入过得单词将从原词库移除并编入该词库，之前的词义将被覆盖"
    )
    if not {'单词', '词义'} <= set(columns):
        raise ValueError('单词列表文件需包含 “单词” 和 “词义” 两列')
    for idx, row in word_list.iterrows():
        Word.objects.update_or_create(
            defaults={
                "word": row['单词'],
                "chinese": row['词义'],
                "symbol": row.get('音标') or None,
                "library": library
            },
            word=row['单词']
        )
    print(
        f"导入完成！\n"
        f"现总词数：{Word.objects.count()}\n"
        f"全部词库：{list(WordLibrary.objects.all().values_list('name', flat=True))}"
    )
    return word_list.shape[0], Word.objects.all().count()
