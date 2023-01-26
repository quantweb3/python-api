# 回放行情所需
import datetime
import hashlib
import json
import time

from chanlun import fun
from chanlun.backtesting.base import MarketDatas
from chanlun.cl_interface import *
from chanlun.exchange.exchange_db import ExchangeDB
from tqdm.auto import tqdm
from chanlun import cl

from typing import Dict


class BackTestKlines(MarketDatas):
    """
    数据库行情回放
    """

    def __init__(self, market: str, start_date: str, end_date: str, frequencys: List[str], cl_config=None):
        """
        配置初始化
        :param market: 市场 支持 a hk currency
        :param frequencys:
        :param start_date:
        :param end_date:
        """
        super().__init__(market, frequencys, cl_config)

        self.market = market
        self.base_code = None
        self.frequencys = frequencys
        self.cl_config = cl_config
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        self.start_date = start_date
        if isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
        self.end_date = end_date

        self.now_date: datetime.datetime = start_date

        # 是否使用 cache 保存所有k线数据，True 会将代码周期时间段内所有数据读取并保存到内存，False 在每次使用的时候从数据库中获取
        # True 在多代码时会占用太多内存，这时可以设置为 False 增加使用数据库按需获取，增加运行时间，减少占用内存空间
        self.load_data_to_cache = True
        self.load_kline_nums = 10000  # 每次重新加载的K线数量
        self.cl_data_kline_max_nums = 50000  # 缠论数据中最大保存的k线数量

        # 保存k线数据
        self.all_klines: Dict[str, pd.DataFrame] = {}

        # 每个周期缓存的k线数据，避免多次请求重复计算
        self.cache_klines: Dict[str, Dict[str, pd.DataFrame]] = {}

        self.ex = ExchangeDB(self.market)

        # 用于循环的日期列表
        self.loop_datetime_list: Dict[str, list] = {}

        # 进度条
        self.bar: Union[tqdm, None] = None

        self.time_fmt = '%Y-%m-%d %H:%M:%S'

        # 统计时间
        self._use_times = {
            'klines': 0,
            'convert_klines': 0,
            'get_cl_data': 0,
        }

    def init(self, base_code: str, frequency: Union[str, list]):
        # 初始化，获取循环的日期列表
        self.base_code = base_code
        if frequency is None:
            frequency = [self.frequencys[-1]]
        if isinstance(frequency, str):
            frequency = [frequency]
        for f in frequency:
            klines = self.ex.klines(
                base_code, f,
                start_date=fun.datetime_to_str(self.start_date), end_date=fun.datetime_to_str(self.end_date),
                args={'limit': None}
            )
            self.loop_datetime_list[f] = list(klines['date'].to_list())

        self.bar = tqdm(total=len(list(self.loop_datetime_list.values())[-1]))

    def clear_all_cache(self):
        """
        清除所有可用缓存，释放内存
        """
        self.cache_klines = {}
        self.all_klines = {}
        self.cache_cl_datas = {}
        self.cl_datas = {}
        return True

    def next(self, frequency: str = ''):
        if frequency == '' or frequency is None:
            frequency = self.frequencys[-1]
        if len(self.loop_datetime_list[frequency]) == 0:
            self.clear_all_cache()
            return False
        self.now_date = self.loop_datetime_list[frequency].pop(0)
        for f, loop_dt_list in self.loop_datetime_list.items():
            self.loop_datetime_list[f] = [d for d in loop_dt_list if d >= self.now_date]
        # 清除之前的 cl_datas 、klines 缓存，重新计算
        self.cache_cl_datas = {}
        self.cache_klines = {}
        self.bar.update(1)
        return True

    def last_k_info(self, code) -> dict:
        kline = self.klines(code, self.frequencys[-1])
        return {
            'date': kline.iloc[-1]['date'],
            'open': float(kline.iloc[-1]['open']),
            'close': float(kline.iloc[-1]['close']),
            'high': float(kline.iloc[-1]['high']),
            'low': float(kline.iloc[-1]['low']),
        }

    def get_cl_data(self, code, frequency, cl_config: dict = None) -> ICL:
        _time = time.time()
        try:
            # 根据回测配置，可自定义不同周期所使用的缠论配置项
            if cl_config is None:
                if code in self.cl_config.keys():
                    cl_config = self.cl_config[code]
                elif frequency in self.cl_config.keys():
                    cl_config = self.cl_config[frequency]
                elif 'default' in self.cl_config.keys():
                    cl_config = self.cl_config['default']
                else:
                    cl_config = self.cl_config

            # 将配置项md5哈希，并加入到 key 中，这样可以保存并获取多个缠论配置项的数据
            cl_config_key = json.dumps(cl_config)
            cl_config_key = hashlib.md5(cl_config_key.encode(encoding='UTF-8')).hexdigest()

            key = '%s_%s_%s' % (code, frequency, cl_config_key)
            if key in self.cache_cl_datas.keys():
                return self.cache_cl_datas[key]

            if key not in self.cl_datas.keys():
                # 第一次进行计算
                klines = self.klines(code, frequency)
                self.cl_datas[key] = cl.CL(code, frequency, cl_config).process_klines(klines)
            else:
                # 更新计算
                cd = self.cl_datas[key]

                # 节省内存，最多存 n k线数据，超过就清空重新计算，必须要大于每次K线获取的数量
                if self.cl_data_kline_max_nums is not None and len(cd.get_klines()) >= self.cl_data_kline_max_nums:
                    self.cl_datas[key] = cl.CL(code, frequency, cl_config)
                    cd = self.cl_datas[key]

                klines = self.klines(code, frequency)

                if len(klines) > 0:
                    if len(cd.get_klines()) == 0:
                        self.cl_datas[key].process_klines(klines)
                    else:
                        # 判断是追加更新还是从新计算
                        cl_end_time = cd.get_klines()[-1].date
                        kline_start_time = klines.iloc[0]['date']
                        if cl_end_time > kline_start_time:
                            self.cl_datas[key].process_klines(klines)
                        else:
                            self.cl_datas[key] = cl.CL(code, frequency, cl_config).process_klines(klines)

            # 回测单次循环周期内，计算过后进行缓存，避免多次计算
            self.cache_cl_datas[key] = self.cl_datas[key]

            return self.cache_cl_datas[key]
        finally:
            self._use_times['get_cl_data'] += time.time() - _time

    def klines(self, code, frequency) -> pd.DataFrame:
        if code in self.cache_klines.keys() and len(self.cache_klines[code][frequency]) > 0:
            # 直接从缓存中读取
            return self.cache_klines[code][frequency]

        _time = time.time()
        klines = {}
        if self.load_data_to_cache:
            # 使用缓存
            for f in self.frequencys:
                key = '%s-%s' % (code, f)
                if key not in self.all_klines.keys():
                    # 从数据库获取日期区间的所有行情
                    self.all_klines[key] = self.ex.klines(
                        code, f,
                        start_date=self._cal_start_date_by_frequency(self.start_date, f),
                        end_date=fun.datetime_to_str(self.end_date),
                        args={'limit': None}
                    )

            for f in self.frequencys:
                key = '%s-%s' % (code, f)
                if self.market in ['currency', 'futures']:
                    kline = self.all_klines[key][self.all_klines[key]['date'] < self.now_date][-self.load_kline_nums::]
                else:
                    kline = self.all_klines[key][self.all_klines[key]['date'] <= self.now_date][-self.load_kline_nums::]
                klines[f] = kline
        else:
            # 使用数据库按需查询
            for f in self.frequencys:
                klines[f] = self.ex.klines(code, f, end_date=fun.datetime_to_str(self.now_date), args={'limit': 10000})
        self._use_times['klines'] += time.time() - _time

        # 转换周期k线，去除未来数据
        klines = self.convert_klines(klines)
        # 将结果保存到 缓存中，避免重复读取
        self.cache_klines[code] = klines
        return klines[frequency]

    def convert_klines(self, klines: Dict[str, pd.DataFrame]):
        """
        转换 kline，去除未来的 kline数据
        :return:
        """
        # 合成周期对应的低级别k线数量（也要兼顾不同市场的时间周期）
        # frequency_num_maps = {
        #     'd': {'4h': 7, '60m': 25, '30m': 50, '15m': 100, '5m': 300},
        #     '4h': {'60m': 5, '30m': 10, '15m': 20, '5m': 60, '1m': 300},
        #     '60m': {'30m': 3, '15m': 6, '5m': 20, '1m': 70},
        #     '30m': {'15m': 3, '5m': 10, '1m': 35},
        #     '15m': {'5m': 5, '1m': 20},
        #     '5m': {'1m': 10},
        # }
        _time = time.time()
        for i in range(len(self.frequencys), 1, -1):
            min_f = self.frequencys[i - 1]
            max_f = self.frequencys[i - 2]
            if len(klines[min_f]) == 0:
                continue
            new_kline = self.ex.convert_kline_frequency(klines[min_f][-120::], max_f)
            if len(klines[max_f]) > 0 and len(new_kline) > 0:
                klines[max_f] = klines[max_f].append(new_kline).drop_duplicates(subset=['date'], keep='last')
                # 删除大周期中，日期大于最小周期的未来数据
                klines[max_f] = klines[max_f].drop(
                    klines[max_f][klines[max_f]['date'] > klines[min_f].iloc[-1]['date']].index
                )
        self._use_times['convert_klines'] += time.time() - _time
        return klines

    def _cal_start_date_by_frequency(self, start_date: datetime, frequency) -> str:
        """
        按照周期，计算行情获取的开始时间
        :param start_date :
        :param frequency:
        :return:
        """
        market_days_freq_maps = {
            'a': {'w': 10000, 'd': 10000, '120m': 500, '4h': 500, '60m': 100, '30m': 700, '15m': 350, '5m': 150,
                  '1m': 5},
            'hk': {'d': 5000, '120m': 500, '4h': 500, '60m': 100, '30m': 100, '15m': 50, '5m': 25, '1m': 5},
            'us': {'d': 5000, '120m': 500, '4h': 500, '60m': 100, '30m': 100, '15m': 50, '5m': 25, '1m': 5},
            'currency': {'w': 2000, 'd': 2000, '4h': 1000, '120m': 500, '60m': 210, '30m': 105, '15m': 55, '10m': 25,
                         '5m': 18, '1m': 4},
            'futures': {'d': 5000, '120m': 500, '4h': 500, '60m': 500, '30m': 500, '15m': 480, '10m': 240, '5m': 300,
                        '1m': 60},
        }
        for _freq in ['w', 'd', '120m', '4h', '60m', '30m', '15m', '10m', '5m', '1m']:
            if _freq == frequency:
                return (start_date - datetime.timedelta(days=market_days_freq_maps[self.market][_freq])).strftime(
                    self.time_fmt)
        raise Exception(f'不支持的周期 {frequency}')
