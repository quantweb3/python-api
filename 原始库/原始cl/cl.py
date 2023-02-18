import datetime
from typing import List, Dict

import numpy as np
import pandas as pd
import talib as ta


class Kline:
    """
    原始K线对象
    """

    def __init__(self, index: int, date: datetime, h: float, l: float, o: float, c: float, a: float):
        self.index: int = index
        self.date: datetime = date
        self.h: float = h
        self.l: float = l
        self.o: float = o
        self.c: float = c
        self.a: float = a

    def __str__(self):
        return "index: %s date: %s h: %s l: %s o: %s c:%s a:%s" % \
               (self.index, self.date, self.h, self.l, self.o, self.c, self.a)


class CLKline:
    """
    缠论K线对象
    """

    def __init__(self, k_index: int, date: datetime, h: float, l: float, o: float, c: float, a: float,
                 klines: List[Kline] = [], index: int = 0, _n: int = 0, _q: bool = False):
        self.k_index: int = k_index
        self.date: datetime = date
        self.h: float = h
        self.l: float = l
        self.o: float = o
        self.c: float = c
        self.a: float = a
        self.klines: List[Kline] = klines  # 其中包含K线对象
        self.index: int = index
        self.n: int = _n  # 记录包含的K线数量
        self.q: bool = _q  # 是否有缺口
        self.up_qs = None  # 合并时之前的趋势

    def __str__(self):
        return "index: %s k_index:%s date: %s h: %s l: %s _n:%s _q:%s" % \
               (self.index, self.k_index, self.date, self.h, self.l, self.n, self.q)


class FX:
    """
    分型对象
    """

    def __init__(self, _type: str, k: CLKline, klines: List[CLKline], val: float,
                 index: int = 0, tk: bool = False, real: bool = True, done: bool = True):
        self.type: str = _type  # 分型类型 （ding 顶分型 di 底分型）
        self.k: CLKline = k
        self.klines: List[CLKline] = klines
        self.val: float = val
        self.index: int = index
        self.tk: bool = tk  # 记录是否跳空
        self.real: bool = real  # 是否是有效的分型
        self.done: bool = done  # 分型是否完成

    def ld(self):
        """
        分型力度值，数值越大表示分型力度越大
        根据第三根K线与前两根K线的位置关系决定
        """
        ld = 0
        one_k = self.klines[0]
        two_k = self.klines[1]
        three_k = self.klines[2]
        if three_k is None:
            return ld
        if self.type == 'ding':
            if three_k.h < (two_k.h - (two_k.h - two_k.l) / 2):
                # 第三个K线的高点，低于第二根的50%以下
                ld += 1
            if three_k.l < one_k.l and three_k.l < two_k.l:
                # 第三个最低点是三根中最低的
                ld += 1
        elif self.type == 'di':
            if three_k.l > (two_k.l + (two_k.h - two_k.l) / 2):
                # 第三个K线的低点，低于第二根的50%之上
                ld += 1
            if three_k.h > one_k.h and three_k.h > two_k.h:
                # 第三个最低点是三根中最低的
                ld += 1
        return ld

    def high(self):
        """
        获取分型最高点
        """
        high = self.klines[0].h
        for k in self.klines:
            if k is not None:
                high = max(high, k.h)
        return high

    def low(self):
        """
        获取分型的最低点
        """
        low = self.klines[0].l
        for k in self.klines:
            if k is not None:
                low = min(low, k.l)
        return low

    def __str__(self):
        return 'index: %s type: %s real: %s date : %s val: %s done: %s' % (
            self.index, self.type, self.real, self.k.date, self.val, self.done)


class LINE:
    """
    线的基本定义，笔和线段继承此对象
    """

    def __init__(self, start: FX, end: FX, high: float, low: float, _type: str, ld: dict, done: bool, index: int):
        self.start: FX = start  # 线的起始位置，以分型来记录
        self.end: FX = end  # 线的结束位置，以分型来记录
        self.high: float = high
        self.low: float = low
        self.type: str = _type  # 线的方向类型 （up 上涨  down 下跌）
        self.ld: dict = ld  # 记录线的力度信息
        self.done: bool = done  # 线是否完成
        self.index: int = index  # 线的索引，后续查找方便


class ZS:
    """
    中枢对象（笔中枢，线段中枢）
    """

    def __init__(self, zs_type: str, start: FX, end: FX = None, zg: float = None, zd: float = None,
                 gg: float = None, dd: float = None, _type: str = None, index: int = 0, line_num: int = 0,
                 level: int = 0, is_high_kz: bool = False, max_ld: dict = None):
        self.zs_type: str = zs_type  # 标记中枢类型 bi 笔中枢 xd 线段中枢
        self.start: FX = start
        self.lines: List[LINE, BI, XD] = []  # 中枢，记录中枢的线（笔 or 线段）对象
        self.end: FX = end
        self.zg: float = zg
        self.zd: float = zd
        self.gg: float = gg
        self.dd: float = dd
        self.type: str = _type  # 中枢类型（up 上涨中枢  down 下跌中枢  zd 震荡中枢）
        self.index: int = index
        self.line_num: int = line_num  # 中枢包含的 笔或线段 个数
        self.level: int = level  # 中枢级别 0 本级别 1 上一级别 ...
        self.max_ld: dict = max_ld  # 记录中枢中最大笔力度
        self.done = False  # 记录中枢是否完成
        self.real = True  # 记录是否是有效中枢

    def add_line(self, line: LINE):
        """
        添加 笔 or 线段
        """
        self.lines.append(line)
        return True

    def zf(self):
        """
        中枢振幅
        """
        return ((self.gg - self.dd) / (self.zg - self.zd) - 1) * 100

    def __str__(self):
        return 'index: %s zs_type: %s level: %s FX: (%s-%s) type: %s zg: %s zd: %s gg: %s dd: %s done: %s' % \
               (self.index, self.zs_type, self.level, self.start.index, self.end.index, self.type, self.zg, self.zd,
                self.gg, self.dd,
                self.done)


class MMD:
    """
    买卖点对象
    """

    def __init__(self, name: str, zs: ZS):
        # print(  "买卖点名称:")
        # print(  name )
        self.name: str = name  # 买卖点名称
        self.zs: ZS = zs  # 买卖点对应的中枢对象

    def __str__(self):
        
        
        return 'MMD: %s ZS: %s' % (self.name, self.zs)


class BC:
    """
    背驰对象
    """

    def __init__(self, _type: str, zs: ZS, pre_line: LINE, bc: bool):
        
        
        # print(  "背驰类型:")
        # print(  _type )
        self.type: str = _type  # 背驰类型 （bi 笔背驰 xd 线段背驰 pz 盘整背驰 qs 趋势背驰）
        self.zs: ZS = zs  # 背驰对应的中枢
        self.pre_line: LINE = pre_line  # 比较的笔 or 线段
        self.bc = bc  # 是否背驰

    def __str__(self):
        # print(  "背驰类型:")
        # print(  self.type)
        return 'BC type: %s bc: %s zs: %s' % (self.type, self.bc, self.zs)


class BI(LINE):
    """
    笔对象
    """

    def __init__(self, start: FX, end: FX = None, high: float = None, low: float = None, _type: str = None,
                 ld: dict = None, done: bool = None, index: int = 0, td: bool = False, fx_num: int = 0):
        super().__init__(start, end, high, low, _type, ld, done, index)
        self.mmds: List[MMD] = []  # 买卖点
        self.bcs: List[BC] = []  # 背驰信息
        self.td: bool = td  # 笔是否停顿
        self.fx_num: int = fx_num  # 包含的分型数量

    def __str__(self):
        return 'index: %s type: %s FX: (%s - %s) high: %s low: %s done: %s' % \
               (self.index, self.type, self.start.index, self.end.index, self.high, self.low, self.done)

    def add_mmd(self, name: str, zs: ZS):
        """
        添加买卖点
        """
        self.mmds.append(MMD(name, zs))
        return True

    def line_mmds(self):
        """
        返回当前笔所有买卖点名称
        """
        return list(set([m.name for m in self.mmds]))

    def line_bcs(self):
        return [_bc.type for _bc in self.bcs]

    def mmd_exists(self, check_mmds: list):
        """
        检查当前笔是否包含指定的买卖点的一个
        """
        mmds = self.line_mmds()
        return len(set(check_mmds) & set(mmds)) > 0

    def bc_exists(self, bc_type: list):
        """
        检查是否有背驰的情况
        """
        bc = False
        for _bc in self.bcs:
            if _bc.type in bc_type and _bc.bc:
                bc = True
                break
        return bc

    def add_bc(self, _type: str, zs: [ZS, None], pre_line: LINE, bc: bool):
        """
        添加背驰点
        """
        self.bcs.append(BC(_type, zs, pre_line, bc))
        return True


class XLFX:
    """
    线段序列分型
    """

    def __init__(self, _type: str, high: float, low: float, bi: BI, qk: bool = False, fx_high: float = None,
                 fx_low: float = None, done: bool = True):
        self.type = _type
        self.high = high
        self.low = low
        self.bi = bi

        self.qk = qk  # 分型是否有缺口
        self.fx_high = fx_high  # 三个分型特征序列的最高点
        self.fx_low = fx_low  # 三个分型特征序列的最低点

        self.done = done  # 序列分型是否完成

    def __str__(self):
        return "XLFX type : %s high : %s low : %s bi : %s" % (self.type, self.high, self.low, self.bi)


class XD(LINE):
    """
    线段对象
    """

    def __init__(self, start: FX, end: FX, start_bi: BI, end_bi: BI = None, _type: str = None, high: float = None,
                 low: float = None,
                 ding_fx: XLFX = None, di_fx: XLFX = None, ld: dict = None, index: int = 0, done: bool = True):
        super().__init__(start, end, high, low, _type, ld, done, index)

        self.start_bi: BI = start_bi  # 线段起始笔
        self.end_bi: BI = end_bi  # 线段结束笔
        self.mmds: List[MMD] = []  # 买卖点
        self.bcs: List[BC] = []  # 背驰信息
        self.ding_fx: XLFX = ding_fx
        self.di_fx: XLFX = di_fx

    def add_mmd(self, name: str, zs: ZS):
        """
        添加买卖点
        """
        self.mmds.append(MMD(name, zs))
        return True

    def line_mmds(self):
        """
        返回当前线段所有买卖点名称
        """
        return list(set([m.name for m in self.mmds]))

    def line_bcs(self):
        return [_bc.type for _bc in self.bcs]

    def mmd_exists(self, check_mmds: list):
        """
        检查当前笔是否包含指定的买卖点的一个
        """
        mmds = self.line_mmds()
        return len(set(check_mmds) & set(mmds)) > 0

    def bc_exists(self, bc_type: list):
        """
        检查是否有背驰的情况
        """
        bc = False
        for _bc in self.bcs:
            if _bc.type in bc_type and _bc.bc:
                bc = True
                break
        return bc

    def add_bc(self, _type: str, zs: [ZS, None], pre_line: LINE, bc: bool):
        """
        添加背驰点
        """
        self.bcs.append(BC(_type, zs, pre_line, bc))
        return True

    def __str__(self):
        return 'XD index: %s type: %s start: % end: %s high: %s low: %s done: %s' % (
            self.index, self.type, self.start_bi.index, self.end_bi.index, self.high, self.low, self.done
        )


class QS:
    """
    趋势对象
    """

    def __init__(self, qs_type: str, start_line: LINE, end_line: LINE = None, zss: List[ZS] = None, _type='zd'):
        self.qs_type: str = qs_type  # 趋势的类型，bi 笔中枢组成的趋势 xd 线段中枢组成的趋势
        self.start_line: LINE = start_line  # 趋势的起始线
        self.end_line: LINE = end_line  # 趋势的结束线
        self.zss: List[ZS] = zss  # 趋势包含的中枢列表
        self.type: str = _type  # 趋势方向类型 （up 上涨趋势 zd 震荡趋势 down 下跌趋势）

    def __str__(self):
        return 'QS qsType: %s Type %s start: %s end: %s ZSS %s' % (
            self.type, self.qs_type, self.start_line.index, self.end_line.index, len(self.zss))


class CL:
    """
    行情数据缠论分析
    """

    def __init__(self, code: str, frequency: str, config: [dict, None] = None):
        """
        缠论计算
        :param code: 代码
        :param frequency: 周期
        :param config: 配置
        """
        self.code = code
        self.frequency = frequency
        self.config = config if config else {}
        print(">>>>>>>>>>>>>>>>>Zen<<<<<<<<<<<<<<<<<")

        # 是否标识出未完成的笔， True 标识，False 不标识
        if 'no_bi' not in self.config:
            self.config['no_bi'] = False
        # 是否标识未完成的线段，True 标识，False 不标识
        if 'no_xd' not in self.config:
            self.config['no_xd'] = False
        # 笔类型 old  老笔  new 新笔  dd 顶底成笔
        if 'bi_type' not in self.config:
            self.config['bi_type'] = 'old'
        # 分型是否允许包含成笔的配置，False 不允许分型包含成笔，True 允许分型包含成笔
        if 'fx_baohan' not in self.config:
            self.config['fx_baohan'] = False

        # 指标配置项
        idx_keys = {
            'idx_macd_fast': 12,
            'idx_macd_slow': 26,
            'idx_macd_signal': 9,
            'idx_boll_period': 20,
            'idx_ma_period': 5,
        }
        for _k in idx_keys.keys():
            if _k not in self.config:
                self.config[_k] = idx_keys[_k]
            else:
                self.config[_k] = int(self.config[_k])

        # 计算后保存的值
        self.klines: List[Kline] = []  # 整理后的原始K线
        self.cl_klines: List[CLKline] = []  # 缠论K线
        self.idx: dict = {
            'macd': {'dea': [], 'dif': [], 'hist': []},
            'ma': [],
            'boll': {'up': [], 'mid': [], 'low': []},
        }  # 各种行情指标
        self.fxs: List[FX] = []  # 分型列表
        self.bis: List[BI] = []  # 笔列表
        self.xds: List[XD] = []  # 线段列表
        self.bi_zss: List[ZS] = []  # 笔中枢列表
        self.bi_qss: List[QS] = []  # 笔趋势列表
        self.xd_zss: List[ZS] = []  # 线段中枢列表
        self.xd_qss: List[QS] = []  # 线段趋势列表

        # 用于保存计算线段的序列分型
        self.__xl_ding = []
        self.__xl_di = []
        self.__xlfx_ding = []
        self.__xlfx_di = []

        self._use_time = 0  # debug 调试用时

    def process_klines(self, klines: pd.DataFrame):
        """
        计算k线缠论数据
        传递 pandas 数据，需要包括以下列：
            date  时间日期  datetime 格式
            high  最高价
            low   最低价
            open  开盘价
            close  收盘价
            volume  成交量

        可增量多次调用，重复已计算的会自动跳过，最后一个 bar 会进行更新
        """
        k_index = len(self.klines)
        for _k in klines.iterrows():
            k = _k[1]
            if len(self.klines) == 0:
                nk = Kline(index=k_index, date=k['date'], h=float(k['high']), l=float(k['low']),
                           o=float(k['open']), c=float(k['close']), a=float(k['volume']))
                self.klines.append(nk)
                k_index += 1
                continue
            if self.klines[-1].date > k['date']:
                continue
            if self.klines[-1].date == k['date']:
                self.klines[-1].h = float(k['high'])
                self.klines[-1].l = float(k['low'])
                self.klines[-1].o = float(k['open'])
                self.klines[-1].c = float(k['close'])
                self.klines[-1].a = float(k['volume'])
            else:
                nk = Kline(index=k_index, date=k['date'], h=float(k['high']), l=float(k['low']),
                           o=float(k['open']), c=float(k['close']), a=float(k['volume']))
                self.klines.append(nk)
                k_index += 1
            self.process_idx()
            self.process_cl_kline()
            self.process_fx()
            if self.process_bi():
                # 有新笔产生，才更新以下数据
                self.process_xd()
                self.process_zs(['bi', 'xd'])
                self.process_qs(['bi', 'xd'])
                self.process_mmd(['bi', 'xd'])

        return self

    def process_idx(self):
        """
        计算指标
        """
        if len(self.klines) < 2:
            return False

        prices = [k.c for k in self.klines[-100:]]
        # 计算 macd
        macd_dif, macd_dea, macd_hist = ta.MACD(np.array(prices),
                                                fastperiod=self.config['idx_macd_fast'],
                                                slowperiod=self.config['idx_macd_slow'],
                                                signalperiod=self.config['idx_macd_signal'])
        # macd = {'dea': macd_dea, 'dif': macd_dif, 'hist': macd_hist}

        # 计算 ma
        ma = ta.MA(np.array(prices), timeperiod=self.config['idx_ma_period'])

        # 计算 BOLL 指标
        boll_up, boll_mid, boll_low = ta.BBANDS(np.array(prices), timeperiod=self.config['idx_boll_period'])

        for i in range(2, 0, -1):
            index = self.klines[-i].index
            if (len(self.idx['ma']) - 1) >= index:
                # 更新操作
                self.idx['ma'][index] = ma[-i]
                self.idx['macd']['dea'][index] = macd_dea[-i]
                self.idx['macd']['dif'][index] = macd_dif[-i]
                self.idx['macd']['hist'][index] = macd_hist[-i]
                self.idx['boll']['up'][index] = boll_up[-i]
                self.idx['boll']['mid'][index] = boll_mid[-i]
                self.idx['boll']['low'][index] = boll_low[-i]
            else:
                # 添加操作
                self.idx['ma'].append(ma[-i])
                self.idx['macd']['dea'].append(macd_dea[-i])
                self.idx['macd']['dif'].append(macd_dif[-i])
                self.idx['macd']['hist'].append(macd_hist[-i])
                self.idx['boll']['up'].append(boll_up[-i])
                self.idx['boll']['mid'].append(boll_mid[-i])
                self.idx['boll']['low'].append(boll_low[-i])
        #
        # self.idx = {
        #     'macd': macd,
        #     'boll': {'up': boll_up, 'mid': boll_mid, 'low': boll_low}
        # }
        return True

    def process_cl_kline(self):
        """
        根据最后一个 k 线，检查包含关系，生成缠论K线
        """
        k = self.klines[-1]  # 最后一根K线对象
        if len(self.cl_klines) == 0:
            cl_kline = CLKline(date=k.date, k_index=k.index, h=k.h, l=k.l, o=k.o, c=k.c, a=k.a, klines=[k], _n=1,
                               _q=False, index=0)
            self.cl_klines.append(cl_kline)
            return True

        # 传递之前两个的缠论K线，用来判断趋势（不包括最后两个）
        up_cl_klines = self.cl_klines[-4:-2]

        # 最后两个缠论K线，重新进行包含处理
        cl_kline_1 = self.cl_klines[-1]
        cl_kline_2 = self.cl_klines[-2] if len(self.cl_klines) >= 2 else None
        klines = cl_kline_2.klines if cl_kline_2 else []
        klines += cl_kline_1.klines
        if k.date != klines[-1].date:
            klines.append(k)

        cl_klines = self.klines_baohan(klines, up_cl_klines)
        if (len(cl_klines) >= 2 and cl_kline_2) or (len(cl_klines) == 1 and cl_kline_2):
            # 重新给缠论k线附新值
            cl_kline_2.k_index = cl_klines[0].k_index
            cl_kline_2.date = cl_klines[0].date
            cl_kline_2.h = cl_klines[0].h
            cl_kline_2.l = cl_klines[0].l
            cl_kline_2.o = cl_klines[0].o
            cl_kline_2.c = cl_klines[0].c
            cl_kline_2.a = cl_klines[0].a
            cl_kline_2.klines = cl_klines[0].klines
            cl_kline_2.n = cl_klines[0].n
            cl_kline_2.q = cl_klines[0].q
            cl_kline_2.up_qs = cl_klines[0].up_qs

            if len(cl_klines) == 1:
                # 之前有两个缠论K线，新合并的只有一个了，之前最后一个删除
                cl_kline_1 = None
                del (self.cl_klines[-1])
            del (cl_klines[0])

        if cl_kline_1 and len(cl_klines) > 0:
            cl_kline_1.k_index = cl_klines[0].k_index
            cl_kline_1.date = cl_klines[0].date
            cl_kline_1.h = cl_klines[0].h
            cl_kline_1.l = cl_klines[0].l
            cl_kline_1.o = cl_klines[0].o
            cl_kline_1.c = cl_klines[0].c
            cl_kline_1.a = cl_klines[0].a
            cl_kline_1.klines = cl_klines[0].klines
            cl_kline_1.n = cl_klines[0].n
            cl_kline_1.q = cl_klines[0].q
            cl_kline_1.up_qs = cl_klines[0].up_qs
            del (cl_klines[0])

        for ck in cl_klines:
            ck.index = self.cl_klines[-1].index + 1
            self.cl_klines.append(ck)

        return True

    def process_fx(self):
        """
        根据最后一个缠论K线，计算分型
        """
        if len(self.cl_klines) < 3:
            return False

        up_k = self.cl_klines[-3]
        now_k = self.cl_klines[-2]
        end_k = self.cl_klines[-1]
        fx = None
        if (up_k.h < now_k.h and now_k.h > end_k.h) and (up_k.l < now_k.l and now_k.l > end_k.l):
            tiaokong = True if (up_k.h < now_k.l or now_k.l > end_k.h) else False
            fx = FX(index=0, _type='ding', k=now_k, klines=[up_k, now_k, end_k], val=now_k.h, tk=tiaokong, real=True,
                    done=True)
        if (up_k.h > now_k.h and now_k.h < end_k.h) and (up_k.l > now_k.l and now_k.l < end_k.l):
            tiaokong = True if (up_k.l > now_k.h or now_k.h < end_k.l) else False
            fx = FX(index=0, _type='di', k=now_k, klines=[up_k, now_k, end_k], val=now_k.l, tk=tiaokong, real=True,
                    done=True)

        if fx is None:
            if self.config['no_bi']:
                # 检测未完成符合条件的分型
                up_k = self.cl_klines[-2]
                now_k = self.cl_klines[-1]
                end_k = None
                if now_k.h > up_k.h:
                    fx = FX(index=0, _type='ding', k=now_k, klines=[up_k, now_k, end_k], val=now_k.h, tk=False,
                            real=True,
                            done=False)
                elif now_k.l < up_k.l:
                    fx = FX(index=0, _type='di', k=now_k, klines=[up_k, now_k, end_k], val=now_k.l, tk=False, real=True,
                            done=False)
                else:
                    return False
            else:
                return False

        if len(self.fxs) == 0 and fx.done is False:
            return False
        elif len(self.fxs) == 0 and fx.done is True:
            self.fxs.append(fx)
            return True

        # 检查和上个分型是否是一个，是就重新算
        is_update = False  # 标识本次是否是更新分型
        end_fx = self.fxs[-1]
        if fx.k.index == end_fx.k.index:
            end_fx.k = fx.k
            end_fx.klines = fx.klines
            end_fx.val = fx.val
            end_fx.tk = fx.tk
            end_fx.done = fx.done
            end_fx.real = fx.real
            fx = end_fx
            is_update = True

        # 检查分型有效性，根据上一个有效分型，进行检查
        up_fx = None
        # 记录区间中无效分型的最大最小值
        fx_qj_high = None
        fx_qj_low = None
        for _fx in self.fxs[::-1]:
            if is_update and _fx.index == fx.index:
                continue
            fx_qj_high = _fx.val if fx_qj_low is None else max(fx_qj_high, _fx.val)
            fx_qj_low = _fx.val if fx_qj_low is None else min(fx_qj_low, _fx.val)
            if _fx.real:
                up_fx = _fx
                break

        if up_fx is None:
            return False

        if self.config['bi_type'] == 'dd':
            if is_update is False:
                fx.index = self.fxs[-1].index + 1
                self.fxs.append(fx)
            return True

        if fx.type == 'ding' and up_fx.type == 'ding' and up_fx.k.h <= fx.k.h:
            # 连续两个顶分型，前面的低于后面的，只保留后面的，前面的去掉
            up_fx.real = False
        elif fx.type == 'di' and up_fx.type == 'di' and up_fx.k.l >= fx.k.l:
            # 连续两个底分型，前面的高于后面的，只保留后面的，前面的去掉
            up_fx.real = False
        elif fx.type == up_fx.type:
            # 相邻的性质，必然前顶不能低于后顶，前底不能高于后底，遇到相同的，只保留第一个
            fx.real = False
        elif fx.type == 'ding' and up_fx.type == 'di' \
                and (
                fx.k.h <= up_fx.k.l
                or fx.k.l <= up_fx.k.h
                # or fx.val < fx_qj_high
                or (self.config['fx_baohan'] is False and fx.high() < up_fx.high())  # 是否允许分型包含的判断
        ):
            # 当前分型 顶，上一个分型 底，当 顶 低于 底， 或者 当前分型不是区间中最高的，是个无效的顶，跳过
            fx.real = False
        elif fx.type == 'di' and up_fx.type == 'ding' \
                and (
                fx.k.l >= up_fx.k.h
                or fx.k.h >= up_fx.k.l
                # or fx.val > fx_qj_low
                or (self.config['fx_baohan'] is False and fx.low() > up_fx.low())  # 是否允许分型包含的判断
        ):
            # 当前分型 底，上一个分型 顶 ，当 底 高于 顶，或者 当前分型不是区间中最低的，是个无效顶底，跳过
            fx.real = False
        else:
            if self.config['bi_type'] == 'old' and fx.k.index - up_fx.k.index < 4:
                # 老笔 顶与底之间缠论 K线 数量至少 5 根
                fx.real = False
            if self.config['bi_type'] == 'new' and \
                    (fx.k.index - up_fx.k.index < 3 or fx.k.klines[-1].index - up_fx.k.klines[0].index < 4):
                # 新笔  进行包含处理，顶底在内至少4根独立K线  还原包含关系，顶底在内至少5根K线
                fx.real = False

        if is_update is False:
            fx.index = self.fxs[-1].index + 1
            self.fxs.append(fx)
        return True

    def process_bi(self):
        """
        根据最后的分型，找到对应的笔
        """
        if len(self.fxs) == 0:
            return False

        # 检查最后一笔的起始分型是否有效，无效则删除笔
        if len(self.bis) > 0 and self.bis[-1].start.real is False:
            del (self.bis[-1])

        bi = self.bis[-1] if len(self.bis) > 0 else None

        # 如果笔存在，检查是否有笔分型停顿
        if bi:
            close = self.klines[-1].c
            if bi.done and bi.type == 'up' and close < bi.end.klines[-1].l:
                bi.td = True
            elif bi.done and bi.type == 'down' and close > bi.end.klines[-1].h:
                bi.td = True
            else:
                bi.td = False

        if bi is None:
            real_fx = [_fx for _fx in self.fxs if _fx.real]
            if len(real_fx) < 2:
                return False
            for fx in real_fx:
                if bi is None:
                    bi = BI(start=fx, index=0)
                    continue
                if bi.start.type == fx.type:
                    continue
                bi.end = fx
                bi.type = 'up' if bi.start.type == 'di' else 'down'
                bi.high = max(bi.start.val, bi.end.val)
                bi.low = min(bi.start.val, bi.end.val)
                bi.done = fx.done
                bi.td = False
                bi.fx_num = bi.end.index - bi.start.index
                self.process_line_ld(bi)  # 计算笔力度
                self.bis.append(bi)
                return True

        # 确定最后一个有效分型
        end_real_fx = None
        for _fx in self.fxs[::-1]:
            if _fx.real:
                end_real_fx = _fx
                break
        if bi.end.real is False and bi.end.type == end_real_fx.type:
            bi.end = end_real_fx
            bi.high = max(bi.start.val, bi.end.val)
            bi.low = min(bi.start.val, bi.end.val)
            bi.done = end_real_fx.done
            bi.fx_num = bi.end.index - bi.start.index
            self.process_line_ld(bi)  # 计算笔力度
            return True

        if bi.end.index < end_real_fx.index and bi.end.type != end_real_fx.type:
            # 新笔产生了
            new_bi = BI(start=bi.end, end=end_real_fx)
            new_bi.index = self.bis[-1].index + 1
            new_bi.type = 'up' if new_bi.start.type == 'di' else 'down'
            new_bi.high = max(new_bi.start.val, new_bi.end.val)
            new_bi.low = min(new_bi.start.val, new_bi.end.val)
            new_bi.done = end_real_fx.done
            new_bi.td = False
            new_bi.fx_num = new_bi.end.index - new_bi.start.index
            self.process_line_ld(new_bi)  # 计算笔力度
            self.bis.append(new_bi)
            return True
        return False

    def process_xd(self):
        """
        根据最后笔，生成特征序列，计算线段
        """

        if len(self.xds) == 0:
            dings = self.cal_xd_xlfx(self.bis, 'ding')
            dis = self.cal_xd_xlfx(self.bis, 'di')
            if len(dings) <= 0 or len(dis) <= 0:
                return False
            xlfxs = dings + dis
            xlfxs.sort(key=lambda xl: xl.bi.index)
            xlfxs = self.merge_xd_xlfx(xlfxs)
            if len(xlfxs) < 2:
                return False

            if xlfxs[0].type == 'di':
                xd_type = 'up'
                di_fx = xlfxs[0]
                ding_fx = xlfxs[1]
                done = ding_fx.done
            else:
                xd_type = 'down'
                di_fx = xlfxs[1]
                ding_fx = xlfxs[0]
                done = di_fx.done

            # 根据配置，是否显示未完成线段
            if self.config['no_xd'] is False and done is False:
                return False

            start_bi = xlfxs[0].bi
            end_bi = self.bis[xlfxs[1].bi.index - 1]
            xd = XD(
                start=start_bi.start,
                end=end_bi.end,
                start_bi=start_bi,
                end_bi=end_bi,
                _type=xd_type,
                high=max(start_bi.high, end_bi.high),
                low=min(start_bi.low, end_bi.low),
                ding_fx=ding_fx,
                di_fx=di_fx,
                done=done,
            )
            self.process_line_ld(xd)
            self.xds.append(xd)
            return True

        up_xd = self.xds[-1]
        if up_xd.done is True:
            dings = self.cal_xd_xlfx(self.bis[up_xd.end_bi.index:], 'ding')
            dis = self.cal_xd_xlfx(self.bis[up_xd.end_bi.index:], 'di')
        else:
            dings = self.cal_xd_xlfx(self.bis[up_xd.start_bi.index:], 'ding')
            dis = self.cal_xd_xlfx(self.bis[up_xd.start_bi.index:], 'di')

        if len(dings) == 0 and len(dis) == 0:
            return False

        if up_xd.type == 'up' and up_xd.done and len(dis) > 0:
            # 上一个线段是向上的，找底分型
            for di in dis:
                # 根据配置，是否显示未完成线段
                if self.config['no_xd'] is False and di.done is False:
                    continue
                if di.bi.index - up_xd.end_bi.index >= 2 and di.low < up_xd.high:
                    # 判断第二种情况，有缺口，后续的分型继续 跌破/突破 前高/前低
                    if up_xd.ding_fx.qk and up_xd.ding_fx.fx_high < di.fx_high:
                        continue
                    start_bi = self.bis[up_xd.end_bi.index + 1]
                    end_bi = self.bis[di.bi.index - 1]
                    xd = XD(
                        start=start_bi.start,
                        end=end_bi.end,
                        start_bi=start_bi,
                        end_bi=end_bi,
                        _type='down',
                        high=max(start_bi.high, end_bi.high),
                        low=min(start_bi.low, end_bi.low),
                        index=up_xd.index + 1,
                        ding_fx=up_xd.ding_fx,
                        di_fx=di,
                        done=di.done
                    )
                    self.process_line_ld(xd)
                    self.xds.append(xd)
                    return True
        if up_xd.type == 'down' and up_xd.done and len(dings) > 0:
            # 上一个线段是向下的，找顶分型
            for ding in dings:
                # 根据配置，是否显示未完成线段
                if self.config['no_xd'] is False and ding.done is False:
                    continue
                if ding.bi.index - up_xd.end_bi.index >= 2 and ding.high > up_xd.low:
                    # 判断第二种情况，有缺口，后续的分型继续 跌破/突破 前高/前低
                    if up_xd.di_fx.qk and up_xd.di_fx.fx_low > ding.fx_low:
                        continue
                    start_bi = self.bis[up_xd.end_bi.index + 1]
                    end_bi = self.bis[ding.bi.index - 1]
                    xd = XD(
                        start=start_bi.start,
                        end=end_bi.end,
                        start_bi=start_bi,
                        end_bi=end_bi,
                        _type='up',
                        high=max(start_bi.high, end_bi.high),
                        low=min(start_bi.low, end_bi.low),
                        index=up_xd.index + 1,
                        ding_fx=ding,
                        di_fx=up_xd.di_fx,
                        done=ding.done
                    )
                    self.process_line_ld(xd)
                    self.xds.append(xd)
                    return True

        if up_xd.type == 'up' and len(dings) > 0:
            # 上一个线段是向上的，之后又出现了顶分型，进行线段的修正
            for ding in dings:
                # 根据配置，是否显示未完成线段
                if self.config['no_xd'] is False and ding.done is False:
                    continue
                if ding.high >= up_xd.high:
                    end_bi = self.bis[ding.bi.index - 1]
                    up_xd.end = end_bi.end
                    up_xd.end_bi = end_bi
                    up_xd.high = ding.high
                    up_xd.ding_fx = ding
                    up_xd.done = ding.done
                    self.process_line_ld(up_xd)
            return True

        if up_xd.type == 'down' and len(dis) > 0:
            # 上一个线段是向下的，之后有出现了底分型，进行线段的修正
            for di in dis:
                # 根据配置，是否显示未完成线段
                if self.config['no_xd'] is False and di.done is False:
                    continue
                if di.low <= up_xd.low:
                    end_bi = self.bis[di.bi.index - 1]
                    up_xd.end = end_bi.end
                    up_xd.end_bi = end_bi
                    up_xd.low = di.low
                    up_xd.di_fx = di
                    up_xd.done = di.done
                    self.process_line_ld(up_xd)
            return True

        return False

    def process_zs(self, run_types=None):
        """
        根据最后一线（笔 or 线段），计算中枢
        """
        if run_types is None:
            return False
        for run_type in run_types:
            # 根据运行的中枢类型，获取对应的 线（笔 or 线段）
            if run_type == 'bi':
                lines: List[LINE] = self.bis
                zss: List[ZS] = self.bi_zss
            elif run_type == 'xd':
                lines: List[LINE] = self.xds
                zss: List[ZS] = self.xd_zss
            else:
                raise Exception('计算中枢 run_type 定义错误 %s' % run_type)

            if len(lines) < 4:
                return False
            if len(zss) == 0:
                _ls = lines[-4:]
                _zs = self.create_zs(run_type, None, _ls)
                if _zs:
                    zss.append(_zs)
                return True

            line = lines[-1]
            # 获取所有未完成的中枢，依次根据最新的笔进行重新计算
            for _zs in zss:
                if _zs.done:
                    continue
                if _zs.end.index == line.end.index:
                    continue
                # 调用创建中枢，属于更新一次中枢属性
                self.create_zs(run_type, _zs, lines[_zs.lines[0].index:line.index + 1])
                # 如当前线与中枢最后一线格了一线，则中枢已完成
                if line.index - _zs.lines[-1].index > 1:
                    _zs.done = True
                    if len(_zs.lines) < 5:  # 中枢笔小于5线为无效中枢  进入一线 + 3 + 离开一线
                        _zs.real = False

            # 以新线为基础，创建中枢
            _zs = self.create_zs(run_type, None, lines[-4:])
            if _zs:
                # 检查是否已经有这个中枢了
                is_exists = False
                for __zs in zss[::-1]:
                    if __zs.start.index == _zs.start.index:
                        is_exists = True
                        break
                if is_exists is False:
                    _zs.index = zss[-1].index + 1
                    zss.append(_zs)

        return True

    def process_qs(self, run_types=None):
        """
        计算当前趋势（已经成型的）
        """
        if run_types is None:
            return False

        for run_type in run_types:
            if run_type == 'bi':
                lines: List[BI] = self.bis
                zss: List[ZS] = self.bi_zss
                qss: List[QS] = self.bi_qss
            elif run_type == 'xd':
                lines: List[XD] = self.xds
                zss: List[ZS] = self.xd_zss
                qss: List[QS] = self.xd_qss
            else:
                raise Exception('计算趋势 run type 错误 %s' % run_type)

            if len(zss) == 0:
                return True
            line = lines[-1]
            # 最后一个趋势是否有延续
            if len(qss) > 0:
                end_qs = qss[-1]
                zss = [_zs for _zs in zss if
                       (end_qs.start_line.start.index <= _zs.start.index and _zs.end.index <= line.end.index)]
                _qss = self.find_zs_qss(run_type, zss)
                for _qs in _qss:
                    if _qs.type == end_qs.type and \
                            _qs.start_line.start.index == end_qs.start_line.start.index and \
                            _qs.end_line.end.index != end_qs.end_line.index:
                        end_qs.zss = _qs.zss
                        end_qs.end_line = _qs.end_line

            # 计算之后的中枢
            start_line = qss[-1].end_line if len(qss) > 0 else lines[0]
            zss = [_zs for _zs in zss if
                   (start_line.start.index <= _zs.start.index and _zs.end.index <= line.end.index)]
            _qss = self.find_zs_qss(run_type, zss)
            for _qs in _qss:
                if _qs.type == 'up' or _qs.type == 'down':
                    # 只保留有方向的趋势，震荡趋势就不保存了
                    qss.append(_qs)

        return True

    def process_mmd(self, run_types=None):
        """
        计算背驰与买卖点
        """
        if run_types is None:
            return False

        for run_type in run_types:
            if run_type == 'bi':
                lines: List[BI] = self.bis
                zss: List[ZS] = self.bi_zss
                qss: List[QS] = self.bi_qss
            elif run_type == 'xd':
                lines: List[XD] = self.xds
                zss: List[ZS] = self.xd_zss
                qss: List[QS] = self.xd_qss
            else:
                raise Exception('记录买卖点 run_type 错误 ：%s' % run_type)

            if len(zss) == 0:
                return True

            line = lines[-1]
            # 清空买卖点与背驰情况，重新计算
            line.bcs = []
            line.mmds = []

            # 笔背驰添加
            line.add_bc(run_type, None, lines[-3], self.beichi_line(lines[-3], line))
            # 查找所有以当前线为结束的中枢
            line_zss = [_zs for _zs in zss if (_zs.lines[-1].index == line.index and _zs.real and _zs.level == 0)]
            for _zs in line_zss:
                line.add_bc('pz', _zs, _zs.lines[0], self.beichi_pz(_zs, line))
                line.add_bc('qs', _zs, _zs.lines[0], self.beichi_qs(qss[-1] if len(qss) > 0 else None, _zs, line))

            # 买卖点的判断
            # 一类买卖点，有趋势背驰，记为一类买卖点
            for bc in line.bcs:
                if bc.type == 'qs' and bc.bc:
                    if line.type == 'up':
                        line.add_mmd('1sell', bc.zs)
                    if line.type == 'down':
                        line.add_mmd('1buy', bc.zs)

            # 二类买卖点，同向的前一笔突破，再次回拉不破，或者背驰，即为二类买卖点
            for _zs in line_zss:
                if len(_zs.lines) < 7:
                    continue
                tx_line: [BI, XD] = _zs.lines[-3]
                if _zs.lines[0].type == 'up' and line.type == 'up':
                    if tx_line.high == _zs.gg and (tx_line.high > line.high or tx_line.bc_exists(['pz', 'qs'])):
                        line.add_mmd('2sell', _zs)
                if _zs.lines[0].type == 'down' and line.type == 'down':
                    if tx_line.low == _zs.dd and (tx_line.low < line.low or tx_line.bc_exists(['pz', 'qs'])):
                        line.add_mmd('2buy', _zs)

            # 类二买卖点，当前中枢的第一笔是二类买卖点，并且离开中枢的力度比进入的力度弱，则为类二买卖点
            for _zs in line_zss:
                # 如果中枢笔中包含反方向买卖点或者背驰，则不在出类二买卖点了
                have_buy = False
                have_sell = False
                have_bc = False
                for _line in _zs.lines[:-1]:
                    # 不包括当前笔
                    if _line.mmd_exists(['1buy', '2buy', 'l2buy', '3buy', 'l3buy']):
                        have_buy = True
                    if _line.mmd_exists(['1sell', '2sell', 'l2sell', '3sell', 'l3sell']):
                        have_sell = True
                    if _line.bc_exists(['pz', 'qs']):
                        have_bc = True
                if '2buy' in _zs.lines[1].line_mmds() and line.type == 'down':
                    if have_sell is False and have_bc is False and self.compare_ld_beichi(_zs.lines[1].ld, line.ld):
                        line.add_mmd('l2buy', _zs)
                if '2sell' in _zs.lines[1].line_mmds() and line.type == 'up':
                    if have_buy is False and have_bc is False and self.compare_ld_beichi(_zs.lines[1].ld, line.ld):
                        line.add_mmd('l2sell', _zs)

            # 三类买卖点，需要找中枢结束笔是前一笔的中枢
            line_3mmd_zss = [_zs for _zs in zss if
                             (_zs.lines[-1].index == line.index - 1 and _zs.real and _zs.level == 0)]
            for _zs in line_3mmd_zss:
                if len(_zs.lines) < 5:
                    continue
                if line.type == 'up' and line.high < _zs.zd:
                    line.add_mmd('3sell', _zs)
                if line.type == 'down' and line.low > _zs.zg:
                    line.add_mmd('3buy', _zs)

            # 类三类买卖点，同类二买卖点差不多
            for _zs in line_zss:
                # 如果中枢笔中包含反方向买卖点或者背驰，则不在出类三买卖点了
                have_buy = False
                have_sell = False
                have_bc = False
                for _line in _zs.lines[:-1]:
                    # 不包括当前笔
                    if _line.mmd_exists(['1buy', '2buy', 'l2buy', '3buy', 'l3buy']):
                        have_buy = True
                    if _line.mmd_exists(['1sell', '2sell', 'l2sell', '3sell', 'l3sell']):
                        have_sell = True
                    if _line.bc_exists(['pz', 'qs']):
                        have_bc = True
                for mmd in _zs.lines[1].mmds:
                    if mmd.name == '3buy':
                        if have_sell is False and have_bc is False and line.type == 'down' \
                                and line.low > mmd.zs.zg \
                                and self.compare_ld_beichi(_zs.lines[0].ld, line.ld):
                            line.add_mmd('l3buy', mmd.zs)
                    if mmd.name == '3sell':
                        if have_buy is False and have_bc is False and line.type == 'up' \
                                and line.high < mmd.zs.zd \
                                and self.compare_ld_beichi(_zs.lines[0].ld, line.ld):
                            line.add_mmd('l3sell', mmd.zs)

        return True

    def beichi_line(self, pre_line: LINE, now_line: LINE):
        """
        计算两线之间是否有背驰，两笔必须是同方向的，最新的线创最高最低记录
        背驰 返回 True，否则返回 False
        """
        if pre_line.type != now_line.type:
            return False
        if pre_line.type == 'up' and now_line.high < pre_line.high:
            return False
        if pre_line.type == 'down' and now_line.low > pre_line.low:
            return False

        return self.compare_ld_beichi(pre_line.ld, now_line.ld)

    def beichi_pz(self, zs: ZS, now_line: LINE):
        """
        判断中枢是否有盘整背驰，中枢最后一线要创最高最低才可比较

        """
        if zs.lines[-1].index != now_line.index:
            return False
        if zs.type not in ['up', 'down']:
            return False

        return self.compare_ld_beichi(zs.lines[0].ld, now_line.ld)

    def beichi_qs(self, qs: QS, zs: ZS, now_line: LINE):
        """
        判断是否是趋势背驰，首先需要看之前是否有不重合的同向中枢，在进行背驰判断
        """
        if qs is None:
            # 无趋势无背驰
            return False

        if zs.lines[-1].index != now_line.index:
            return False
        # 趋势最后一个中枢，是否和当前中枢是一个（根据 index 判断）
        if qs.zss[-1].index != zs.index or qs.zss[-1].lines[-1].index != now_line.index:
            return False
        # 最后两个中枢的级别要一致
        if qs.zss[-1].level != qs.zss[-2].level:
            return False
        # 趋势中枢与笔方向是否一致
        if qs.zss[-1].type != now_line.type:
            return False
        # 两个趋势之间的力度，与离开中枢的力度做对比
        qj_ld = self.query_macd_ld(qs.zss[-2].end, qs.zss[-1].start)
        qj_ld = {'macd': qj_ld}
        return self.compare_ld_beichi(qj_ld, now_line.ld)

    def create_zs(self, zs_type: str, zs: [ZS, None], lines: List[LINE]) -> [ZS, None]:
        """
        根据线，获取是否有共同的中枢区间
        zs_type 标记中枢类型（笔中枢 or 线段中枢）
        lines 中，第一线是进入中枢的，不计算高低，最后一线不一定是最后一个出中枢的，如果是最后一个出中枢的，则不需要计算高低点
        """
        if len(lines) < 3:
            return None

        # 进入段要笔中枢第一段高或低
        if lines[0].type == 'up' and lines[0].low > lines[1].low:
            return None
        if lines[0].type == 'down' and lines[0].high < lines[1].high:
            return None

        if zs is None:
            zs = ZS(zs_type=zs_type, start=lines[1].start, _type='zd')
        zs.lines = []
        zs.add_line(lines[0])

        zs_fanwei = [lines[1].high, lines[1].low]
        zs_gg = lines[1].high
        zs_dd = lines[1].low
        for i in range(1, len(lines)):
            # 当前线的交叉范围
            _l = lines[i]
            cross_fanwei = self.cross_qujian(zs_fanwei, [_l.high, _l.low])
            if cross_fanwei is None:
                break

            # 下一线的交叉范围
            if i < len(lines) - 1:
                next_line = lines[i + 1]
                next_fanwei = self.cross_qujian(zs_fanwei, [next_line.high, next_line.low])
            else:
                next_fanwei = True

            if next_fanwei:
                zs_gg = max(zs_gg, _l.high)
                zs_dd = min(zs_dd, _l.low)
                if i <= 2:
                    zs_fanwei = [cross_fanwei['max'], cross_fanwei['min']]
                # 根据笔数量，计算级别
                zs.line_num = len(zs.lines) - 1
                zs.level = int(zs.line_num / 9)
                zs.end = _l.end
                # 记录中枢中，最大的笔力度
                if zs.max_ld is None:
                    zs.max_ld = _l.ld
                elif _l.ld:
                    zs.max_ld = zs.max_ld if self.compare_ld_beichi(zs.max_ld, _l.ld) else _l.ld
            zs.add_line(_l)

        # 看看中枢笔数是否足够
        if len(zs.lines) < 4:
            return None

        zs.zg = zs_fanwei[0]
        zs.zd = zs_fanwei[1]
        zs.gg = zs_gg
        zs.dd = zs_dd

        # 计算中枢方向
        if zs.lines[0].type == zs.lines[-1].type:
            if zs.lines[0].type == 'up' and zs.lines[0].low < zs.dd and zs.lines[-1].high >= zs.gg:
                zs.type = zs.lines[0].type
            elif zs.lines[0].type == 'down' and zs.lines[0].high > zs.gg and zs.lines[-1].low <= zs.dd:
                zs.type = zs.lines[0].type
            else:
                zs.type = 'zd'
        else:
            zs.type = 'zd'

        return zs

    def process_line_ld(self, line: LINE):
        """
        处理并计算线（笔、线段）的力度
        """
        line.ld = {
            'macd': self.query_macd_ld(line.start, line.end)
        }
        return True

    def query_macd_ld(self, start_fx: FX, end_fx: FX):
        """
        计算分型区间 macd 力度
        """
        if start_fx.index > end_fx.index:
            raise Exception('%s - %s - %s 计算力度，开始分型不可以大于结束分型' % (self.code, self.frequency, self.klines[-1].date))

        dea = np.array(self.idx['macd']['dea'][start_fx.k.k_index:end_fx.k.k_index + 1])
        dif = np.array(self.idx['macd']['dif'][start_fx.k.k_index:end_fx.k.k_index + 1])
        hist = np.array(self.idx['macd']['hist'][start_fx.k.k_index:end_fx.k.k_index + 1])
        if len(hist) == 0:
            hist = np.array([0])
        if len(dea) == 0:
            dea = np.array([0])
        if len(dif) == 0:
            dif = np.array([0])

        hist_abs = abs(hist)
        hist_up = np.array([_i for _i in hist if _i > 0])
        hist_down = np.array([_i for _i in hist if _i < 0])
        hist_sum = hist_abs.sum()
        hist_up_sum = hist_up.sum()
        hist_down_sum = hist_down.sum()
        end_dea = dea[-1]
        end_dif = dif[-1]
        end_hist = hist[-1]
        return {
            'dea': {'end': end_dea, 'max': np.max(dea), 'min': np.min(dea)},
            'dif': {'end': end_dif, 'max': np.max(dif), 'min': np.min(dif)},
            'hist': {'sum': hist_sum, 'up_sum': hist_up_sum, 'down_sum': hist_down_sum, 'end': end_hist},
        }

    @staticmethod
    def cal_xd_xlfx(bis: List[BI], fx_type='ding'):
        """
        计算线段序列分型
        """
        xulie = []
        for bi in bis:
            if (fx_type == 'ding' and bi.type == 'down') or (fx_type == 'di' and bi.type == 'up'):
                now_xl = {'max': bi.high, 'min': bi.low, 'bi': bi}
                if len(xulie) == 0:
                    xulie.append(now_xl)
                    continue
                qs = 'up' if fx_type == 'ding' else 'down'
                up_xl = xulie[-1]

                if up_xl['max'] >= now_xl['max'] and up_xl['min'] <= now_xl['min']:
                    if qs == 'up':
                        now_xl['bi'] = now_xl['bi'] if now_xl['max'] >= up_xl['max'] else up_xl['bi']
                        now_xl['max'] = max(up_xl['max'], now_xl['max'])
                        now_xl['min'] = max(up_xl['min'], now_xl['min'])
                    else:
                        now_xl['bi'] = now_xl['bi'] if now_xl['min'] <= up_xl['min'] else up_xl['bi']
                        now_xl['max'] = min(up_xl['max'], now_xl['max'])
                        now_xl['min'] = min(up_xl['min'], now_xl['min'])

                    del (xulie[-1])
                    xulie.append(now_xl)
                elif up_xl['max'] <= now_xl['max'] and up_xl['min'] >= now_xl['min']:
                    # 强包含，之后的特征序列包含前面的，形成强转折，这时不处理包含关系
                    xulie.append(now_xl)
                else:
                    xulie.append(now_xl)

        xlfxs: List[XLFX] = []
        for i in range(1, len(xulie)):
            up_xl = xulie[i - 1]
            now_xl = xulie[i]
            if len(xulie) > (i + 1):
                next_xl = xulie[i + 1]
            else:
                next_xl = None

            qk = True if (up_xl['max'] < now_xl['min'] or up_xl['min'] > now_xl['max']) else False
            if next_xl is not None:
                # 已完成分型
                fx_high = max(up_xl['max'], now_xl['max'], next_xl['max'])
                fx_low = min(up_xl['min'], now_xl['min'], now_xl['min'])

                if fx_type == 'ding' and up_xl['max'] <= now_xl['max'] and now_xl['max'] >= next_xl['max']:
                    now_xl['type'] = 'ding'
                    xlfxs.append(
                        XLFX('ding', now_xl['max'], now_xl['min'], now_xl['bi'], qk=qk, fx_high=fx_high, fx_low=fx_low,
                             done=True)
                    )
                if fx_type == 'di' and up_xl['min'] >= now_xl['min'] and now_xl['min'] <= next_xl['min']:
                    now_xl['type'] = 'di'
                    xlfxs.append(
                        XLFX('di', now_xl['max'], now_xl['min'], now_xl['bi'], qk=qk, fx_high=fx_high, fx_low=fx_low,
                             done=True)
                    )

            else:
                # 未完成分型
                fx_high = max(up_xl['max'], now_xl['max'])
                fx_low = min(up_xl['min'], now_xl['min'])

                if fx_type == 'ding' and up_xl['max'] <= now_xl['max']:
                    now_xl['type'] = 'ding'
                    xlfxs.append(
                        XLFX('ding', now_xl['max'], now_xl['min'], now_xl['bi'], qk=qk, fx_high=fx_high, fx_low=fx_low,
                             done=False)
                    )
                if fx_type == 'di' and up_xl['min'] >= now_xl['min']:
                    now_xl['type'] = 'di'
                    xlfxs.append(
                        XLFX('di', now_xl['max'], now_xl['min'], now_xl['bi'], qk=qk, fx_high=fx_high, fx_low=fx_low,
                             done=False)
                    )

        return xlfxs

    @staticmethod
    def merge_xd_xlfx(xlfxs: List[XLFX]):
        """
        合并线段的顶底序列分型，过滤掉无效的分型
        """
        real_xl_fxs = []
        for xl in xlfxs:
            if len(real_xl_fxs) == 0:
                real_xl_fxs.append(xl)
                continue
            up_xl = real_xl_fxs[-1]
            if up_xl.type == 'ding' and xl.type == 'ding':
                # 两个顶序列分型
                if xl.high > up_xl.high:
                    del (real_xl_fxs[-1])
                    real_xl_fxs.append(xl)
            elif up_xl.type == 'di' and xl.type == 'di':
                # 两个低序列分型
                if xl.low < up_xl.low:
                    del (real_xl_fxs[-1])
                    real_xl_fxs.append(xl)
            elif up_xl.type == 'ding' and xl.type == 'di' and up_xl.high < xl.low:
                continue
            elif up_xl.type == 'di' and xl.type == 'ding' and up_xl.low > xl.high:
                continue
            elif xl.bi.index - up_xl.bi.index < 3:  # 不足3笔
                continue
            else:
                real_xl_fxs.append(xl)

        return real_xl_fxs

    @staticmethod
    def compare_ld_beichi(one_ld: dict, two_ld: dict):
        """
        比较两个力度，后者小于前者，返回 True
        :param one_ld:
        :param two_ld:
        :return:
        """
        hist_key = 'sum'
        # if hist_type == 'up':
        #     hist_key = 'up_sum'
        # if hist_type == 'down':
        #     hist_key = 'down_sum'
        if two_ld['macd']['hist'][hist_key] < one_ld['macd']['hist'][hist_key]:
            return True
        else:
            return False

    @staticmethod
    def cross_qujian(qj_one, qj_two):
        """
        计算两个范围相交部分区间
        :param qj_one:
        :param qj_two:
        :return:
        """
        # 判断线段是否与范围值内有相交
        max_one = max(qj_one[0], qj_one[1])
        min_one = min(qj_one[0], qj_one[1])
        max_two = max(qj_two[0], qj_two[1])
        min_two = min(qj_two[0], qj_two[1])

        cross_max_val = min(max_two, max_one)
        cross_min_val = max(min_two, min_one)

        if cross_max_val >= cross_min_val:
            return {'max': cross_max_val, 'min': cross_min_val}
        else:
            return None

    @staticmethod
    def klines_baohan(klines: List[Kline], up_cl_klines: List[CLKline]) -> List[CLKline]:
        """
        k线包含处理，返回缠论k线对象
        """
        cl_klines = []
        cl_kline = CLKline(k_index=klines[0].index, date=klines[0].date,
                           h=klines[0].h, l=klines[0].l, o=klines[0].o, c=klines[0].c, a=klines[0].a,
                           klines=[klines[0]])
        cl_klines.append(cl_kline)
        up_cl_klines.append(cl_kline)

        # if klines[0].date >= datetime.datetime.strptime('2021-06-03 00:00:00', '%Y-%m-%d %H:%M:%S'):
        #     a = 1

        for i in range(1, len(klines)):
            cl_k = cl_klines[-1]
            k = klines[i]
            if (cl_k.h >= k.h and cl_k.l <= k.l) or (k.h >= cl_k.h and k.l <= cl_k.l):
                qushi = 'up' if len(up_cl_klines) >= 2 and up_cl_klines[-2].h < cl_k.h else 'down'
                if qushi == 'up':  # 趋势上涨，向上合并
                    cl_k.k_index = cl_k.k_index if cl_k.h > k.h else k.index
                    cl_k.date = cl_k.date if cl_k.h > k.h else k.date
                    cl_k.h = max(cl_k.h, k.h)
                    cl_k.l = max(cl_k.l, k.l)
                    cl_k.a += k.a  # 交易量累加
                    cl_k.up_qs = 'up'
                else:
                    cl_k.k_index = cl_k.k_index if cl_k.l < k.l else k.index
                    cl_k.date = cl_k.date if cl_k.l < k.l else k.date
                    cl_k.h = min(cl_k.h, k.h)
                    cl_k.l = min(cl_k.l, k.l)
                    cl_k.a += k.a
                    cl_k.up_qs = 'down'
                cl_k.klines.append(k)
                cl_k.n += 1
            else:
                cl_kline = CLKline(k_index=k.index, date=k.date, h=k.h, l=k.l, o=k.o, c=k.c, a=k.a, klines=[k])
                cl_klines.append(cl_kline)
                up_cl_klines.append(cl_kline)

        return cl_klines

    @staticmethod
    def find_zs_qss(qs_type: str, zss: List[ZS]) -> List[QS]:
        """
        查找中枢列表 两两互不关联的中枢
        """
        qss = []
        zss = sorted(zss, key=lambda z: z.index, reverse=False)

        def copy_zs(_zs: ZS) -> ZS:
            """
            复制一个新的中枢对象
            """
            new_zs = ZS(
                zs_type=zs.zs_type,
                start=_zs.start, end=_zs.end, zg=_zs.zg, zd=_zs.zd, gg=_zs.gg, dd=_zs.dd, _type=_zs.type,
                index=_zs.index, line_num=_zs.line_num, level=_zs.level
            )
            new_zs.lines = _zs.lines
            return new_zs

        for zs in zss:
            if zs.type not in ['up', 'down']:
                continue
            qs = None
            start_zs = zs
            for next_zs in zss:
                if next_zs.type != start_zs.type:
                    continue
                if next_zs.index <= start_zs.index:
                    continue
                if (start_zs.gg < next_zs.dd or start_zs.dd > next_zs.gg) and (
                        next_zs.lines[0].index - start_zs.lines[-1].index <= 2):
                    if qs is None:
                        qs = QS(
                            qs_type=qs_type,
                            start_line=start_zs.lines[0],
                            end_line=start_zs.lines[-1],
                            zss=[copy_zs(start_zs)],
                            _type=start_zs.type)
                    qs.zss.append(copy_zs(next_zs))
                    qs.end_bi = next_zs.lines[-1]
                    start_zs = next_zs

            if qs and len(qs.zss) >= 2:
                qss.append(qs)

        return qss


def batch_cls(code, klines: Dict[str, pd.DataFrame], config: dict = None) -> List[CL]:
    """
    批量计算并获取 缠论 数据
    :param code:
    :param klines:
    :param config: 缠论配置
    :return:
    """
    cls = []
    for f in klines.keys():
        cls.append(CL(code, f, config).process_klines(klines[f]))
    return cls


class MultiLevelAnalyse(object):
    """
    缠论多级别分析
    """

    def __init__(self, up_cd: CL, low_cd: CL):
        self.up_cd: CL = up_cd
        self.low_cd: CL = low_cd

    def low_level_qs_by_bi(self, up_bi: BI):
        """
        根据高级别笔，获取其低级别笔的趋势信息
        """
        low_bis = self.__query_low_bis_by_bi(up_bi)
        low_zss = self.__query_low_zss_by_bi(up_bi)

        # 低级别最后一个与高级笔同向的笔
        low_last_bi = low_bis[-1] if len(low_bis) > 0 else None

        # 是否包含至少一个同向的中枢
        same_type_zs = len([_zs for _zs in low_zss if (_zs.type == up_bi.type)])

        qs_done = False
        if len(low_zss) > 0 and low_last_bi and low_last_bi.bc_exists(['pz', 'qs']):
            qs_done = True

        return {
            'zss': low_zss,
            'zs_num': len(low_zss),
            'same_type_zs': same_type_zs,
            'bis': low_bis,
            'bi_num': len(low_bis),
            'last_bi_pz_bc': low_last_bi.bc_exists(['pz']) if low_last_bi is not None else False,
            'last_bi_qs_bc': low_last_bi.bc_exists(['qs']) if low_last_bi is not None else False,
            'last_bi_bi_bc': low_last_bi.bc_exists(['bi']) if low_last_bi is not None else False,
            'low_last_bi': low_last_bi,
            'qs_done': qs_done,
        }

    def up_bi_low_level_qs(self):
        """
        高级别笔，最后一笔的低级别趋势信息
        """
        last_bi = self.up_cd.bis[-1]
        return self.low_level_qs_by_bi(last_bi)

    def __query_low_bis_by_bi(self, up_bi: BI):
        """
        查询高级别笔中包含的低级别的笔，根据高级的笔来查找
        """
        start_date = up_bi.start.k.date
        end_date = up_bi.end.k.date

        low_bis: List[BI] = []
        for _bi in self.low_cd.bis:
            if _bi.start.k.date < start_date:
                continue
            if end_date is not None and _bi.start.k.date > end_date:
                break
            if len(low_bis) == 0 and _bi.type != up_bi.type:
                continue
            low_bis.append(_bi)
        if len(low_bis) > 0 and low_bis[-1].type != up_bi.type:
            del (low_bis[-1])

        return low_bis

    def __query_low_zss_by_bi(self, up_bi: BI):
        """
        查询高级别笔中包含的低级别的中枢，根据高级的笔来查找
        """
        start_date = up_bi.start.k.date
        end_date = up_bi.end.k.date

        low_zss: List[ZS] = []
        for _zs in self.low_cd.bi_zss:
            if start_date <= _zs.start.k.date <= end_date:
                low_zss.append(_zs)

        return low_zss
