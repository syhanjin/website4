# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-13 21:55                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : push.py                                                           =
#    @Program: website                                                         =
# ==============================================================================
import uuid
from typing import List, Union

import httpx

from getui.servers.auth import get_token_str
from getui.servers.utils import build_headers, build_url


def build_push_message(notification):
    return {"notification": notification.get_notification_json()}


def build_android_channel_message(notification):
    if notification.type != "OFFLINE":
        raise ValueError("")
    data = {
        "android": {
            "ups": {
                "notification": notification.get_notification_json(),
                "options": notification.get_options(['HW'])
            }
        }
    }
    return data


def build_message(push=None, channel=None, group_name=None) -> dict:
    if push is None and channel is None:
        raise ValueError("在线推送和离线推送至少包含一个")
    data = {
        "request_id": uuid.uuid4().hex,
    }
    if group_name:
        data["group_name"] = group_name
    if push is not None:
        data["push_message"] = build_push_message(push)
    else:
        data["push_message"] = build_push_message(channel)
    if channel is not None:
        data["push_channel"] = build_android_channel_message(channel)
    return data


def send(url, data) -> (bool, Union[dict, str]):
    token = get_token_str()
    with httpx.Client() as client:
        r = client.post(url, headers=build_headers(token), json=data)
        resp = r.json()
        if resp["code"] == 0:
            return True, resp.get("data")
        else:
            return False, resp["msg"]


def to_single_cid(cid, push=None, channel=None, group_name=None) -> (bool, Union[dict, str]):
    data = build_message(push, channel, group_name)
    data["audience"] = {"cid": [cid]}
    url = build_url("/push/single/cid")
    return send(url, data)


def to_single_alias(alias, push=None, channel=None, group_name=None) -> (bool, Union[dict, str]):
    data = build_message(push, channel, group_name)
    data["audience"] = {"alias": [alias]}
    url = build_url("/push/single/alias")
    return send(url, data)


def to_single_batch_cid(msgs: List[dict], is_async=False):
    data = {
        "is_async": is_async,
        "msg_list": [],
    }
    if len(msgs) > 200:
        raise ValueError("批量推送数组长度不大于 200")
    for msg in msgs:
        msg_data = build_message(
            push=msg.get("push"),
            channel=msg.get("channel"),
            group_name=msg.get("group_name")
        )
        msg_data["audience"] = {"cid": [msg["cid"]]}
        data["msg_list"].append(msg_data)
    url = build_url("/push/single/batch/cid")
    return send(url, data)


def to_single_batch_alias(msgs: List[dict], is_async=False):
    data = {
        "is_async": is_async,
        "msg_list": [],
    }
    if len(msgs) > 200:
        raise ValueError("批量推送数组长度不大于 200")
    for msg in msgs:
        msg_data = build_message(
            push=msg.get("push"),
            channel=msg.get("channel"),
            group_name=msg.get("group_name")
        )
        msg_data["audience"] = {"alias": [msg["alias"]]}
        data["msg_list"].append(msg_data)
    url = build_url("/push/single/batch/alias")
    return send(url, data)


def create_msg(push=None, channel=None, group_name=None) -> (bool, str):
    data = build_message(push, channel, group_name)
    url = build_url("/push/list/message")
    is_success, data = send(url, data)
    if is_success:
        return True, data["taskid"]
    else:
        return False, data


def to_list_cid(
        cid: list, is_async=False, taskid=None, push=None, channel=None, group_name=None
) -> (bool, Union[dict, None], str):
    """
    :return: 是否成功, data, taskid
    """
    if taskid is None:
        is_success, taskid = create_msg(push, channel, group_name)
        if not is_success:
            return False, None, taskid
    data = {
        "audience": {
            "cid": cid
        },
        "taskid": taskid,
        "is_async": is_async
    }
    url = build_url("/push/list/cid")
    is_success, data = send(url, data)
    return is_success, data, taskid


def to_list_alias(
        alias: list, is_async=False, taskid=None, push=None, channel=None, group_name=None
) -> (bool, Union[dict, None], str):
    """
    :return: 是否成功, data, taskid
    """
    if taskid is None:
        is_success, taskid = create_msg(push, channel, group_name)
        if not is_success:
            return False, None, taskid
    data = {
        "audience": {
            "alias": alias
        },
        "taskid": taskid,
        "is_async": is_async
    }
    url = build_url("/push/list/alias")
    is_success, data = send(url, data)
    return is_success, data, taskid


def delete_taskid(taskid):
    url = build_url(f"/task/{taskid}")
    token = get_token_str()
    with httpx.Client() as client:
        r = client.delete(url, headers=build_headers(token))
        resp = r.json()
        return resp


def get_cid_taskid_detail(taskid, cid):
    url = build_url(f"/task/detail/{cid}/{taskid}")
    token = get_token_str()
    with httpx.Client() as client:
        r = client.get(url, headers=build_headers(token))
        resp = r.json()
        if resp["code"] == 0:
            return True, resp["data"]
        else:
            return False, resp["msg"]
