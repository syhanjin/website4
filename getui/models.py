# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-13 21:59                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : models.py                                                         =
#    @Program: website                                                         =
# ==============================================================================
from urllib.parse import quote

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Cid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cids")
    cid = models.CharField(max_length=512, unique=True, editable=False)


class Token(models.Model):
    class Meta:
        ordering = ['-expire_time']

    token = models.CharField(max_length=512, unique=True, editable=False)
    expire_time = models.DateTimeField(editable=False)


class ChannelLevelChoice(models.IntegerChoices):
    l0 = 0, "无声音，无振动，不显示"
    l1 = 1, "无声音，无振动，锁屏不显示，通知栏中被折叠显示，导航栏无logo"
    l2 = 2, "无声音，无振动，锁屏和通知栏中都显示，通知不唤醒屏幕"
    l3 = 3, "有声音，无振动，锁屏和通知栏中都显示，通知唤醒屏幕"
    l4 = 4, "有声音，有振动，亮屏下通知悬浮展示，锁屏通知以默认形式展示且唤醒屏幕"


class ClickTypeOnlineChoice(models.TextChoices):
    INTENT = "intent", "打开应用内特定页面"
    URL = "url", "打开网页地址"
    PAYLOAD = "payload", "自定义消息内容启动应用"
    PAYLOAD_CUSTOM = "payload_custom", "自定义消息内容不启动应用"
    STARTAPP = "startapp", "打开应用首页"
    NONE = "none", "纯通知，无后续动作"


class NotificationMessageOnlineManager(models.Manager):
    def create(self, *args, **kwargs):
        latest = self.first()
        if latest is None:
            kwargs['notify_id'] = 0
        else:
            kwargs['notify_id'] = latest.notify_id + 1
        return super().create(*args, **kwargs)


class NotificationMessageOnline(models.Model):
    """
    在线消息推送
    """

    class Meta:
        ordering = ['-notify_id']

    type = "ONLINE"
    created = models.DateTimeField(verbose_name="生成时间", auto_now_add=True, editable=False)

    title = models.CharField(max_length=50, verbose_name="通知消息标题")

    # 通知消息+长文本样式，与`big_image`二选一，两个都填写时报错，长度 ≤ 512
    body = models.CharField(max_length=256, verbose_name="通知消息内容")

    big_text = models.CharField(max_length=512, verbose_name="长文本消息内容", null=True)

    # 大图的URL地址，通知消息+大图样式， 与`big_text`二选一，两个都填写时报错，URL长度 ≤ 1024
    # big_image = models.OneToOneField('images.Image', on_delete=models.SET_NULL, verbose_name="大图", null=True)

    # 通知的图标名称，包含后缀名（需要在客户端开发时嵌入），如“push.png”，长度 ≤ 64
    # logo = models.CharField(max_length=64, verbose_name="通知图标名称", null=True)

    channel_id = models.CharField(max_length=64, verbose_name="通知渠道id", default="Default")

    channel_name = models.CharField(max_length=64, verbose_name="通知渠道名称", default="Default")

    channel_level = models.PositiveIntegerField(
        verbose_name="设置通知渠道重要性", choices=ChannelLevelChoice.choices, default=ChannelLevelChoice.l3
    )

    click_type = models.CharField(max_length=16, choices=ClickTypeOnlineChoice.choices)

    url = models.URLField(max_length=1024, null=True)

    payload = models.CharField(max_length=3072, verbose_name="点击通知时，附加自定义透传消息", null=True)

    # 覆盖任务时会使用到该字段，两条消息的`notify_id`相同，新的消息会覆盖老的消息，范围：0-2147483647
    notify_id = models.PositiveIntegerField(editable=False, unique=True, primary_key=True)

    """
    角标, 必须大于0, 个推通道下发有效
    此属性目前仅针对华为EMUI4.1及以上设备有效
    角标数字数据会和之前角标数字进行叠加；
    举例：角标数字配置1，应用之前角标数为2，发送此角标消息后，应用角标数显示为3。
    客户端SDK最低要求2.14.0.0
    """
    badge_add_num = models.PositiveIntegerField(verbose_name="角标", default=0)

    objects = NotificationMessageOnlineManager()

    def get_intent(self):
        return "intent://io.dcloud.unipush/?#Intent;scheme=unipush;launchFlags=0x4000000;" \
               "component=com.sakuyark.app/io.dcloud.PandoraEntry;S.UP-OL-SU=true;" \
               f"S.title={quote(self.title)};" \
               f"S.content={quote(self.body)};" \
               f"S.payload={quote(self.payload)};end"

    def get_notification_json(self):
        res = {
            "title": self.title,
            "body": self.body,
            "channel_id": self.channel_id,
            "channel_name": self.channel_name,
            "channel_level": self.channel_level,
            "click_type": self.click_type,
            "notify_id": self.notify_id
        }
        if self.big_text:
            res['big_text'] = self.big_text
        # if self.big_image:
        #     res['big_image'] = settings.HOST_URL + self.big_image.image.url
        # if self.logo:
        #     res['logo'] = self.logo
        if self.click_type == "intent":
            if not self.payload:
                raise ValueError("click_type=intent 必须包含payload")
            res["intent"] = self.get_intent()
        elif self.click_type == "url":
            if not self.url:
                raise ValueError("click_type=url 必须包含url")
            res["url"] = self.url
        elif self.click_type == "payload" or self.click_type == "payload_custom":
            if not self.payload:
                raise ValueError("click_type=payload或payload_custom 必须包含payload")
            res["payload"] = self.payload
        if self.badge_add_num > 0:
            res["badge_add_num"] = self.badge_add_num
        return res


class NotificationMessageOfflineManager(models.Manager):
    def create(self, *args, **kwargs):
        latest = self.first()
        if latest is None:
            kwargs['notify_id'] = 0
        else:
            kwargs['notify_id'] = latest.notify_id + 1
        return super().create(*args, **kwargs)


class ClickTypeOfflineChoice(models.TextChoices):
    INTENT = "intent", "打开应用内特定页面(厂商都支持)"
    URL = "url", "打开网页地址(厂商都支持；华为要求https协议，且游戏类应用不支持打开网页地址)"
    STARTAPP = "startapp", "打开应用首页(厂商都支持)"


class NotificationMessageOffline(models.Model):
    """
    离线厂商推送
    """

    class Meta:
        ordering = ['-notify_id']

    type = "OFFLINE"
    created = models.DateTimeField(verbose_name="生成时间", auto_now_add=True, editable=False)

    title = models.CharField(max_length=20, verbose_name="通知栏标题")
    body = models.CharField(max_length=50, verbose_name="通知栏内容")
    big_text = models.CharField(max_length=512, verbose_name="长文本", null=True)
    click_type = models.CharField(max_length=16, choices=ClickTypeOfflineChoice.choices)
    url = models.URLField(max_length=1024)
    payload = models.CharField(max_length=3836)

    # 覆盖任务时会使用到该字段，两条消息的`notify_id`相同，新的消息会覆盖老的消息，范围：0-2147483647
    notify_id = models.PositiveIntegerField(editable=False, unique=True, primary_key=True)

    badge_add_num = models.PositiveIntegerField(verbose_name="角标", default=1)
    objects = NotificationMessageOfflineManager()

    def get_intent(self):
        return "intent://io.dcloud.unipush/?#Intent;scheme=unipush;launchFlags=0x4000000;" \
               "component=com.sakuyark.app/io.dcloud.PandoraEntry;S.UP-OL-SU=true;" \
               f"S.title={quote(self.title)};" \
               f"S.content={quote(self.body)};" \
               f"S.payload={quote(self.payload)};end"

    def get_notification_json(self):
        res = {
            "title": self.title,
            "body": self.body,
            "click_type": self.click_type,
            "notify_id": self.notify_id
        }
        if self.click_type == "intent":
            if not self.payload:
                raise ValueError("click_type=intent 必须包含payload")
            res["intent"] = self.get_intent()
        elif self.click_type == "url":
            if not self.url:
                raise ValueError("click_type=url 必须包含url")
            res["url"] = self.url
        return res

    def get_options(self, names):
        options = {}
        for name in names:
            options[name] = getattr(self, f'get_{name.upper()}_options')()
        return options

    def get_HW_options(self):
        data = {
            "/message/android/notification/badge/class": "io.dcloud.PandoraEntry",
            "/message/android/notification/badge/add_num": self.badge_add_num,
            "/message/android/notification/style": 1,
            "/message/android/notification/big_body": self.big_text or self.body,
            "/message/android/notification/default_sound": True
        }
        return data
