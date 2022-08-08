# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-8 18:26                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : admin.py                                                          =
#    @Program: website                                                         =
# ==============================================================================
import pandas as pd
from django.utils import timezone

from perfection.models.base import PerfectionStudent
from perfection.models.words import Word, WordLibrary, WordsPerfection


def create_words_perfections():
    """
    自动检查，未创建单词打卡的同学自动创建
    :return:
    """
    # 扫描所有打卡学生，选出今天有没有打卡任务且所有任务已完成的人
    # perfections = PerfectionStudent.objects.filter(can_add_words_perfection=True)
    # 逐个发布打卡
    print(' =' * 10)
    now, rest = timezone.now(), False
    print(f'检查并发布打卡-{now.__format__("%Y-%m-%d %H:%M:%S")}')
    if now.weekday() == 6:
        print("今日为星期日，发布的打卡中将不会有新记单词")
        rest = True
    add_cnt, miss_cnt = 0, 0
    for perfection in PerfectionStudent.objects.all():
        if perfection.can_add_words_perfection:
            WordsPerfection.objects.create(
                user=perfection.user,
                rest=rest
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
            miss_cnt += 1
    print(f'发布完毕！共{add_cnt}个新发布，{miss_cnt}个漏打更新')


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
