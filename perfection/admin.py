# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-2 17:47                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : admin.py                                                          =
#    @Program: website                                                         =
# ==============================================================================
import pandas as pd

from perfection.models.base import PerfectionStudent
from perfection.models.words import Word, WordsPerfection


def create_words_perfections():
    """
    自动检查，未创建单词打卡的同学自动创建
    :return:
    """
    # 扫描所有打卡学生，选出今天有没有打卡任务且所有任务已完成的人
    # perfections = PerfectionStudent.objects.filter(can_add_words_perfection=True)
    # 逐个发布打卡
    for perfection in PerfectionStudent.objects.all():
        if perfection.can_add_words_perfection:
            WordsPerfection.objects.create(
                user=perfection.user,
            )
        elif perfection.missed_words_perfection:
            # 扫描漏打的人并更新打卡内容
            latest = perfection.get_latest(perfection.words)
            review = list(latest.review.all())
            review_new = perfection.get_review_words()
            for word in review_new:
                if word not in review:
                    latest.review.add(word)
            latest.save()
            # for word in perfection.get_review_words():
            #     latest.review.add(word)


def load_word_list(path):
    """ **调试完成-正常
    导入单词列表 手动输入词库，出现重复单词将被覆盖
    :param path: 文件(excel)
    :return: 导入数量, 总数
    """
    lib = input('lib: ')
    if not lib:
        return
    word_list = pd.read_excel(path)
    columns = word_list.columns.values.tolist()
    if not {'单词', '词义'} <= set(columns):
        raise ValueError('单词列表文件需包含 “单词” 和 “词义” 两列')
    for idx, row in word_list.iterrows():
        Word.objects.update_or_create(
            defaults={
                "word": row['单词'],
                "chinese": row['词义'],
                "symbol": row.get('音标') or None,
                "lib": lib
            },
            word=row['单词']
        )

    return word_list.shape[0], Word.objects.all().count()
