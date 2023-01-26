import datetime
import hashlib
import os
import pickle
import random
from typing import Union

import pandas as pd

from chanlun import cl, fun, rd, config
from chanlun.cl_interface import ICL
from chanlun.exchange import Exchange


class FileCacheDB(object):
    """
    文件数据对象
    """

    def __init__(self):
        """
        初始化，判断文件并进行创建
        """
        self.home_path = os.path.expanduser('~')
        self.project_path = self.home_path + '/.chanlun_pro'
        if os.path.isdir(self.project_path) is False:
            os.mkdir(self.project_path)
        self.data_path = self.project_path + '/data'
        if os.path.isdir(self.data_path) is False:
            os.mkdir(self.data_path)
        self.klines_path = self.project_path + '/klines'
        if os.path.isdir(self.klines_path) is False:
            os.mkdir(self.klines_path)

        # 如果内部有值变动，则会重新计算
        self.config_keys = [
            'kline_type', 'fx_qj', 'fx_bh', 'bi_type', 'bi_bzh', 'bi_qj', 'bi_fx_cgd',
            'xd_bzh', 'xd_qj', 'zsd_bzh', 'zsd_qj', 'zs_bi_type', 'zs_xd_type', 'zs_qj', 'zs_wzgx',
            'idx_macd_fast', 'idx_macd_slow', 'idx_macd_signal'
        ]

        # 缠论的更新时间，如果与当前保存不一致，需要清空缓存的计算结果，重新计算
        self.cl_update_date = '2022-12-31'
        rd_cl_update_date = rd.Robj().get('__cl_update_date')
        if rd_cl_update_date != self.cl_update_date:
            rd.Robj().set('__cl_update_date', self.cl_update_date)
            self.clear_all_cl_data()

    def get_tdx_klines(self, code: str, frequency: str) -> Union[None, pd.DataFrame]:
        """
        获取缓存在文件中的股票数据
        """
        file_pathname = f"{self.klines_path}/{code.replace('.', '_')}_{frequency}.csv"
        if os.path.isfile(file_pathname) is False:
            return None
        klines = pd.read_csv(file_pathname)
        if len(klines) > 0:
            klines['date'] = pd.to_datetime(klines['date'])

        # 加一个随机概率，去清理历史的缓存，避免太多占用空间
        if random.randint(0, 100) <= 5:
            self.clear_tdx_old_klines()
        return klines

    def save_tdx_klines(self, code: str, frequency: str, kline: pd.DataFrame):
        """
        保存通达信k线数据对象到文件中
        """
        file_pathname = f"{self.klines_path}/{code.replace('.', '_')}_{frequency}.csv"
        kline.to_csv(file_pathname, index=False)
        return True

    def clear_tdx_old_klines(self):
        """
        删除七天前的k线数据，不活跃的，减少占用空间
        """
        del_lt_times = fun.datetime_to_int(datetime.datetime.now()) - (7 * 24 * 60 * 60)
        for filename in os.listdir(self.klines_path):
            if '.csv' in filename and os.path.getmtime(f"{self.klines_path}/{filename}") < del_lt_times:
                os.remove(f'{self.klines_path}/{filename}')
        return True

    def get_web_cl_data(self, market: str, code: str, frequency: str, cl_config: dict, klines: pd.DataFrame) -> ICL:
        """
        获取web缓存的的缠论数据对象
        """
        unique_md5_str = f'{[f"{k}:{v}" for k, v in cl_config.items() if k in self.config_keys]}'
        unique_md5_str += f'{config.xd_zs_max_lines_split}_{config.allow_split_one_line_to_xd}_{config.allow_bi_fx_strict}'
        key = hashlib.md5(unique_md5_str.encode('UTF-8')).hexdigest()
        # 加分布式锁，避免同时访问一个文件造成异常
        lock_name = f'{market}_{code}_{frequency}'
        lock_id = rd.acquire_lock(lock_name)
        try:
            file_pathname = f"{self.data_path}/{market}_{code.replace('/', '_').replace('.', '_')}_{frequency}_{key}.pkl"
            cd: ICL = cl.CL(code, frequency, cl_config)
            try:
                if os.path.isfile(file_pathname):
                    # print(f'{market}-{code}-{frequency} {key} K-Nums {len(klines)} 使用缓存')
                    with open(file_pathname, 'rb') as fp:
                        cd = pickle.load(fp)
                    # 判断缓存中的最后k线是否大于给定的最新一根k线时间，如果小于说明直接有断档，不连续，重新全量重新计算
                    if len(cd.get_klines()) > 0 and len(klines) > 0 and cd.get_klines()[-1].date < klines.iloc[0][
                        'date']:
                        print(f'{market}-{code}-{frequency} {key} K-Nums {len(klines)} 历史数据有错位，重新计算')
                        cd = cl.CL(code, frequency, cl_config)
                else:
                    pass
                    # print(f'{market}-{code}-{frequency} {key} K-Nums {len(klines)} 没有找到缓存，重新计算')
            except Exception as e:
                if os.path.isfile(file_pathname):
                    print(f'获取 web 缓存的缠论数据对象异常 {market} {code} {frequency} - {e}，尝试删除缓存文件重新计算')
                    os.remove(file_pathname)

            cd.process_klines(klines)
            try:
                with open(file_pathname, 'wb') as fp:
                    pickle.dump(cd, fp)
            except Exception as e:
                print(f'写入缓存异常 {market} {code} {frequency} - {e}')
        finally:
            rd.release_lock(lock_name, lock_id)

        # 加一个随机概率，去清理历史的缓存，避免太多占用空间
        if random.randint(0, 100) <= 5:
            self.clear_old_web_cl_data()

        return cd

    def clear_web_cl_data(self, market: str, code: str):
        """
        清除指定市场下标的缠论缓存对象
        """
        for filename in os.listdir(self.data_path):
            try:
                if '.pkl' in filename and f"{market}_{code.replace('/', '_').replace('.', '_')}" in filename:
                    os.remove(f'{self.data_path}/{filename}')
            except Exception:
                pass
        return True

    def clear_old_web_cl_data(self):
        """
        清除时间超过7天的缓存数据
        """
        del_lt_times = fun.datetime_to_int(datetime.datetime.now()) - (7 * 24 * 60 * 60)
        for filename in os.listdir(self.data_path):
            try:
                if '.pkl' in filename and os.path.getmtime(f"{self.data_path}/{filename}") < del_lt_times:
                    os.remove(f'{self.data_path}/{filename}')
            except Exception:
                pass
        return True

    def clear_all_cl_data(self):
        """
        删除所有缓存的计算结果文件
        """
        for filename in os.listdir(self.data_path):
            try:
                if '.pkl' in filename:
                    os.remove(f'{self.data_path}/{filename}')
            except Exception:
                pass
        return True

    def get_low_to_high_cl_data(self, db_ex: Exchange, market: str, code: str, frequency: str, cl_config: dict) -> ICL:
        """
        专门为递归到高级别图表写的方法，初始数据量较多，所以只能从数据库中获取
        计算一次后进行落盘保存，后续读盘进行更新操作，减少重复计算的时间
        建议定时频繁的进行读取，保持更新，避免太多时间不读取，后续造成数据缺失情况
        """

        key = hashlib.md5(
            f'{[f"{k}:{v}" for k, v in cl_config.items() if k in self.config_keys]}'.encode('UTF-8')
        ).hexdigest()
        filename = f'{self.data_path}/{market}_{code.replace("/", "_")}_{frequency}_{key}.pkl'
        cd: ICL
        if os.path.isfile(filename) is False:
            cd = cl.CL(code, frequency, cl_config)
        else:
            with open(filename, 'rb') as fp:
                cd = pickle.load(fp)
        limit = 200000
        if len(cd.get_klines()) > 10000:
            limit = 1000
        klines = db_ex.klines(code, frequency, args={'limit': limit})
        cd.process_klines(klines)
        with open(filename, 'wb') as fp:
            pickle.dump(cd, fp)
        return cd


if __name__ == '__main__':
    from chanlun.cl_utils import query_cl_chart_config
    from chanlun.exchange.exchange_db import ExchangeDB

    market = 'a'
    code = 'SHSE.000001'
    frequency = '5m'
    cl_config = query_cl_chart_config(market, code)
    ex = ExchangeDB(market)

    fdb = FileCacheDB()
    cd = fdb.get_low_to_high_cl_data(ex, market, code, frequency, cl_config)
    print(len(cd.get_klines()))
    print(cd)
