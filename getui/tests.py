# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-15 12:11                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : tests.py                                                          =
#    @Program: website                                                         =
# ==============================================================================
import json

from getui.models import NotificationMessageOffline, NotificationMessageOnline
from getui.servers.push import to_single_batch_alias

data = {
    "title": "今日的单词打卡内容已下发，请查收",
    "body": f"共20个新单词，20个复习单词",
    "big_text": (f"共20个新单词，20个复习单词\n"
                 + f"今天也要记得按时打卡哦~~"),
    "click_type": "intent",
    "payload": json.dumps(
        {
            "action": "open_page",
            "url": f"/pages/perfection/words/words?wp_id=9709d8df-cac0-417b-b43d-8374234c68df"
        }
    )
}
reminds = [
    {
        "push": NotificationMessageOnline.objects.create(**data),
        "channel": NotificationMessageOffline.objects.create(**data),
        "group_name": "2022-08-15_new",
        "alias": "20864903"
    }
]
for remind_batch in range(0, len(reminds), 200):
    is_success, msg = to_single_batch_alias(reminds[remind_batch: remind_batch + 200])
    print(is_success, msg)
