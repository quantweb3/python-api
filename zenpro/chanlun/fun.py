import base64
import hashlib
import hmac
import logging
import time
import urllib.parse
from datetime import timezone

import requests

from chanlun import config
from chanlun.cl_interface import *


def get_logger(filename=None, level=logging.INFO) -> logging.Logger:
    """
    获取一个日志记录的对象
    """
    logger = logging.getLogger(f'{filename}')
    logger.setLevel(level)
    fmt = logging.Formatter('%(asctime)s - %(levelname)s : %(message)s')
    stream_handler = logging.StreamHandler()

    # 判断之前的handle 是否存在，不存在添加
    stream_exists = False
    file_exists = False
    for _h in logger.handlers:
        if isinstance(_h, logging.StreamHandler):
            stream_exists = True
        if isinstance(_h, logging.FileHandler):
            file_exists = True
    if stream_exists is False:
        logger.addHandler(stream_handler)

    if filename and file_exists is False:
        file_handler = logging.FileHandler(filename=filename, encoding='utf-8')
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    return logger


def send_dd_msg(market: str, msg: Union[str, dict]):
    """
    发送钉钉消息
    https://open.dingtalk.com/document/robots/custom-robot-access

    :param market:
    :param msg: 如果类型是 str 则发送文本消息，dict 发送 markdown 消息 (dict demo {'title': '标题', 'text': 'markdown内容'})
    :return:
    """
    dd_info = None
    if market == 'a':
        dd_info = config.DINGDING_KEY_A
    elif market == 'hk':
        dd_info = config.DINGDING_KEY_HK
    elif market == 'us':
        dd_info = config.DINGDING_KEY_US
    elif market == 'currency':
        dd_info = config.DINGDING_KEY_CURRENCY
    elif market == 'futures':
        dd_info = config.DINGDING_KEY_FUTURES
    else:
        raise Exception('没有配置钉钉的信息')

    url = 'https://oapi.dingtalk.com/robot/send?access_token=%s&timestamp=%s&sign=%s'

    def sign():
        timestamp = str(round(time.time() * 1000))
        secret = dd_info['secret']
        secret_enc = secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        _sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return timestamp, _sign

    t, s = sign()
    url = url % (dd_info['token'], t, s)
    if isinstance(msg, str):
        requests.post(url, json={
            'msgtype': 'text',
            'text': {"content": msg},
        })
    else:
        requests.post(url, json={
            'msgtype': 'markdown',
            'markdown': msg
        })
    return True


def timeint_to_str(_t, _format='%Y-%m-%d %H:%M:%S'):
    """
    时间戳转字符串
    :param _t:
    :param _format:
    :return:
    """
    time_arr = time.localtime(int(_t))
    return time.strftime(_format, time_arr)


def timeint_to_datetime(_t, _format='%Y-%m-%d %H:%M:%S'):
    """
    时间戳转日期
    :param _t:
    :param _format:
    :return:
    """
    time_arr = time.localtime(int(_t))
    return str_to_datetime(time.strftime(_format, time_arr), _format)


def str_to_timeint(_t, _format='%Y-%m-%d %H:%M:%S'):
    """
    字符串转时间戳
    :param _t:
    :param _format:
    :return:
    """
    return int(time.mktime(time.strptime(_t, _format)))


def str_to_datetime(_s, _format='%Y-%m-%d %H:%M:%S'):
    """
    字符串转datetime类型
    :param _s:
    :param _format:
    :return:
    """
    return datetime.datetime.strptime(_s, _format)


def datetime_to_str(_dt: datetime.datetime, _format='%Y-%m-%d %H:%M:%S'):
    """
    datetime转字符串
    :param _dt:
    :param _format:
    :return:
    """
    return _dt.strftime(_format)


def datetime_to_int(_dt: datetime.datetime):
    """
    datetime转时间戳
    :param _dt:
    :return:
    """
    return int(time.mktime(_dt.replace(tzinfo=timezone.utc).timetuple()))


def str_add_seconds_to_str(_s, _seconds, _format='%Y-%m-%d %H:%M:%S'):
    """
    字符串日期时间，加上秒数，在返回新的字符串日期
    """
    _time = int(time.mktime(time.strptime(_s, _format)))
    _time += _seconds
    _time = time.localtime(int(_time))
    return time.strftime(_format, _time)


def now_dt():
    """
    返回当前日期字符串
    """
    return datetime_to_str(datetime.datetime.now())
