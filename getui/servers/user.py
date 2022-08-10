# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-9 18:49                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : user.py                                                           =
#    @Program: website                                                         =
# ==============================================================================

from typing import List

# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-9 18:23                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : user.py                                                           =
#    @Program: website                                                         =
# ==============================================================================
import httpx
from django.contrib.auth import get_user_model

from .auth import get_token_str
from .utils import build_headers, build_url

User = get_user_model()


def bind_alias(data_list: list) -> (bool, str):
    """
    【别名】绑定别名
    > 一个cid只能绑定一个别名，若已绑定过别名的cid再次绑定新别名，则前一个别名会自动解绑，并绑定新别名。
    :param data_list: 数据列表 item: {"cid": "", "alias": ""}
    :return: 是否成功, msg
    """
    token = get_token_str()
    url = build_url('/user/alias')
    with httpx.Client() as client:
        r = client.post(url, headers=build_headers(token), json={"data_list": data_list})
        resp = r.json()
        if resp['code'] == 0:
            return True, resp['msg']
        else:
            return False, resp['msg']


def unbind_alias_cid(data_list: list) -> (bool, str):
    """
    【别名】批量解绑别名
    > 批量解除别名与cid的关系
    :param data_list:数据列表 item: {"cid": "", "alias": ""}
    :return:是否成功, msg
    """
    token = get_token_str()
    url = build_url('/user/alias')
    with httpx.Client() as client:
        r = client.request("DELETE", url, headers=build_headers(token), json={"data_list": data_list})
        resp = r.json()
        if resp['code'] == 0:
            return True, resp['msg']
        else:
            return False, resp['msg']


def unbind_alias_all(alias: str) -> (bool, str):
    """
    【别名】解绑所有别名
    > 解绑所有与该别名绑定的cid
    :param alias: 别名
    :return:是否成功, msg
    """
    token = get_token_str()
    url = build_url(f'/user/alias/{alias}')
    with httpx.Client() as client:
        r = client.delete(url, headers=build_headers(token))
        resp = r.json()
        if resp['code'] == 0:
            return True, resp['msg']
        else:
            return False, resp['msg']


def get_cid_status(cids: List[str]) -> List[dict]:
    """
    【用户】查询用户状态
    > 查询用户的状态
    :param cids:
    :return: [$cid: {
        cid_status	String:	cid在线状态，online在线 offline离线
        device_status	String:	设备在线状态，online在线 offline离线
        }]
    """
    token = get_token_str()
    url = build_url(f"/user/status/{','.join(cids)}")
    with httpx.Client() as client:
        r = client.get(url, headers=build_headers(token))
        resp = r.json()
        if resp['code'] == 0:
            return resp['data']
        else:
            raise RuntimeError(resp['msg'])


def get_cid_detail(cids: List[str]) -> (List[dict], List[str]):
    """
    【用户】查询用户信息
    > 查询用户的信息
    :param cids:
    :return: validCids, invalidCids
        validCids: [cid: {	    用户信息列表
                client_app_id	String	应用id
                package_name	String	包名
                device_token	String	厂商token
                phone_type	Number	手机系统 1-安卓 2-ios
                phoneModel	String	机型
                notificationSwitch	Boolean	系统通知栏开关
                createTime	String	首次登录时间
                loginFreq	Number	登录频次
            }]
        invalidCids: [] 	    无效cid列表
    """
    token = get_token_str()
    url = build_url(f"/user/detail/{','.join(cids)}")
    with httpx.Client() as client:
        r = client.get(url, headers=build_headers(token))
        resp = r.json()
        if resp['code'] == 0:
            return resp['data']['validCids'], resp['data']['invalidCids']
        else:
            raise RuntimeError(resp['msg'])


def cid2alias(cid: str) -> str:
    """
    【别名】根据cid查询别名
    > 通过传入的cid查询对应的别名信息
    :param cid:
    :return: alias
    """
    token = get_token_str()
    url = build_url(f"/user/alias/cid/{cid}")
    with httpx.Client() as client:
        r = client.get(url, headers=build_headers(token))
        resp = r.json()
        if resp["code"] == 0:
            return resp["data"]["alias"]
        else:
            raise RuntimeError(resp)


def alias2cid(alias: str) -> List[str]:
    """
    【别名】根据别名查询cid
    > 通过传入的别名查询对应的cid信息
    :param alias:
    :return:
    """
    token = get_token_str()
    url = build_url(f"/user/cid/alias/{alias}")
    with httpx.Client() as client:
        r = client.get(url, headers=build_headers(token))
        resp = r.json()
        if resp["code"] == 0:
            return resp["data"]["cid"]
        else:
            raise RuntimeError(resp)


def cid2user(cid: str) -> User:
    """
    通过cid查询别名后转换为User对象
    :param cid:
    :return: User
    """
    alias = cid2alias(cid)
    user = User.objects.filter(uuid=alias).first()
    return user


def bind_user(cid, user):
    return bind_alias(
        [
            {"cid": cid, "alias": user.uuid}
        ]
    )


def user2cid(user: User) -> List[str]:
    """
    通过User对象查找cid
    :param user:
    :return:
    """
    uuid = user.uuid
    cids = alias2cid(uuid)
    return cids
