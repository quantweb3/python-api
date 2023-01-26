import math
import threading
from typing import Union

from tenacity import retry, stop_after_attempt, wait_random, retry_if_result
from tqsdk import TqApi, TqAuth, TqAccount, TqKq
from tqsdk.objs import Account, Position, Order

from chanlun import config
from chanlun.exchange.exchange import *
import random


class ExchangeTq(Exchange):
    """
    天勤期货行情
    """

    def __init__(self, use_account=False):
        # 是否连接交易账号，如果是需要执行交易的情况下，必须是 True
        self.use_account = use_account

        # tq api 对象
        self.g_api: Union[TqApi, None] = None
        self.g_account: Union[TqAccount, None] = None
        self.g_all_stocks = []

        # 运行的子进程
        self.t = threading.Thread(target=self.thread_run_update)
        self.t.start()

    def thread_run_update(self):
        """
        子进程发送并更新行情请求
        """
        print('启动天勤子进程任务-更新数据')
        while True:
            try:
                if self.g_api is None:
                    time.sleep(1)
                    continue
                # print('等待数据更新')
                update = self.get_api().wait_update(deadline=time.time() + (1 + random.randint(1, 50) / 100))
                time.sleep(1)
                # print(f'数据更新 {update}')
            except Exception as e:
                if '不能在协程中调用' in str(e):
                    time.sleep(1)
                else:
                    print('Update Data wait error：', e)
                    time.sleep(5)

    def get_api(self) -> TqApi:
        """
        获取 天勤API 对象
        """
        if self.g_api is None:
            account = None
            if self.use_account:
                account = self.get_account()
                if account is None:
                    raise Exception('天勤开启交易，但是实例化账户信息失败')
            self.g_api = TqApi(account=account, auth=TqAuth(config.TQ_USER, config.TQ_PWD))

        return self.g_api

    def close_api(self) -> bool:
        if self.g_api is not None:
            self.g_api.close()
            self.g_api = None
        return True

    def get_account(self) -> Union[TqKq, TqAccount, None]:
        # 使用快期的模拟账号
        # if self.g_account is None:
        #     self.g_account = TqKq()
        # return self.g_account

        # 天勤的实盘账号，如果有设置则使用
        if config.TQ_SP_ACCOUNT == '':
            return None
        if self.g_account is None:
            self.g_account = TqAccount(config.TQ_SP_NAME, config.TQ_SP_ACCOUNT, config.TQ_SP_PWD)
        return self.g_account

    def all_stocks(self):
        """
        获取支持的所有股票列表
        :return:
        """
        if len(self.g_all_stocks) > 0:
            return self.g_all_stocks

        codes = []
        for c in ['FUTURE', 'CONT']:
            codes += self.get_api().query_quotes(ins_class=c)
        infos = self.get_api().query_symbol_info(codes)

        for code in codes:
            self.g_all_stocks.append(
                {'code': code, 'name': infos[infos['instrument_id'] == code].iloc[0]['instrument_name']}
            )
        return self.g_all_stocks

    @retry(stop=stop_after_attempt(3), wait=wait_random(min=1, max=5), retry=retry_if_result(lambda _r: _r is None))
    def klines(self, code: str, frequency: str,
               start_date: str = None, end_date: str = None,
               args=None) -> [pd.DataFrame, None]:
        """
        获取 Kline 线
        :param code:
        :param frequency:
        :param start_date:
        :param end_date:
        :param args:
        :return:
        """
        if args is None:
            args = {}
        if 'limit' not in args.keys():
            args['limit'] = 5000
        frequency_maps = {
            'w': 7 * 24 * 60 * 60, 'd': 24 * 60 * 60, '60m': 60 * 60, '30m': 30 * 60, '15m': 15 * 60,
            '10m': 10 * 60, '6m': 6 * 60, '5m': 5 * 60, '3m': 3 * 60, '2m': 2 * 60, '1m': 1 * 60,
            '30s': 30, '10s': 10
        }
        if start_date is not None and end_date is not None:
            raise Exception('期货行情不支持历史数据查询，因为账号不是专业版，没权限')

        # 获取返回的K线
        klines = None
        try_nums = 5
        for i in range(try_nums):
            try:
                klines = self.get_api().get_kline_serial(code, frequency_maps[frequency], args['limit'])
                if klines is not None and len(klines) > 0:
                    break
            except Exception as e:
                print(f'{code} - {frequency} error : {e} 再次重试')
                time.sleep(2)

        if klines is None:
            return None
        klines = klines.dropna()
        if len(klines) == 0:
            return None

        klines.loc[:, 'date'] = klines['datetime'].apply(lambda x: datetime.datetime.fromtimestamp(x / 1e9))
        klines.loc[:, 'code'] = code

        return klines[['code', 'date', 'open', 'close', 'high', 'low', 'volume']]

    def ticks(self, codes: List[str]) -> Dict[str, Tick]:
        """
        获取代码列表的 Tick 信息
        :param codes:
        :return:
        """
        # 循环获取更新后的 tick
        res_ticks = {}
        for code in codes:
            try_nums = 3
            tick = None
            for i in range(try_nums):
                try:
                    tick = self.get_api().get_quote(code)
                    break
                except Exception:
                    time.sleep(1)
            if tick is None:
                continue
            res_ticks[code] = Tick(
                code=code,
                last=0 if math.isnan(tick['last_price']) else tick['last_price'],
                buy1=0 if math.isnan(tick['bid_price1']) else tick['bid_price1'],
                sell1=0 if math.isnan(tick['ask_price1']) else tick['ask_price1'],
                high=0 if math.isnan(tick['highest']) else tick['highest'],
                low=0 if math.isnan(tick['lowest']) else tick['lowest'],
                open=0 if math.isnan(tick['open']) else tick['open'],
                volume=0 if math.isnan(tick['volume']) else tick['volume'],
                rate=0 if math.isnan(tick['pre_settlement']) or math.isnan(tick['last_price']) else round(
                    (tick['last_price'] - tick['pre_settlement']) / tick['pre_settlement'] * 100, 2)
            )
        return res_ticks

    def stock_info(self, code: str) -> [Dict, None]:
        """
        获取股票的基本信息
        :param code:
        :return:
        """
        all_stocks = self.all_stocks()
        return next((stock for stock in all_stocks if stock['code'] == code), {'code': code, 'name': code})

    def now_trading(self):
        """
        返回当前是否是交易时间
        TODO 简单判断 ：9-12 , 13:30-15:00 21:00-02:30
        """
        hour = int(time.strftime('%H'))
        minute = int(time.strftime('%M'))
        if hour in {9, 10, 11, 14, 21, 22, 23, 0, 1} or (hour == 13 and minute >= 30) or (hour == 2 and minute <= 30):
            return True
        return False

    def balance(self) -> Union[Account, None]:
        """
        获取账户资产
        """
        try_nums = 5
        for _ in range(try_nums):
            try:
                return self.get_api().get_account()
            except Exception as e:
                print(f'天勤获取账户资产异常 {e}')
                time.sleep(2)

        return None

    def positions(self, code: str = None) -> Dict[str, Position]:
        """
        获取持仓
        """
        for _ in range(5):
            try:
                if code is None:
                    positions = self.get_api().get_position(symbol=code)
                    return {
                        _code: positions[_code] for _code in positions.keys()
                        if positions[_code]['pos_long'] != 0 or positions[_code]['pos_short'] != 0
                    }
                else:
                    positions = self.get_api().get_position(symbol=code)
                    if positions['pos_long'] != 0 or positions['pos_short'] != 0:
                        return {code: positions}
                    else:
                        return {}
            except Exception as e:
                print(f'天勤获取持仓 {code} 异常 {e}')
                time.sleep(1)
        return {}

    def order(self, code: str, o_type: str, amount: float, args=None):
        """
        下单接口，默认使用盘口的买一卖一价格成交，知道所有手数成交后返回
        """
        if args is None:
            args = {}

        if o_type == 'open_long':
            direction = 'BUY'
            offset = 'OPEN'
        elif o_type == 'open_short':
            direction = 'SELL'
            offset = 'OPEN'
        elif o_type == 'close_long':
            direction = 'SELL'
            offset = 'CLOSE'
        elif o_type == 'close_short':
            direction = 'BUY'
            offset = 'CLOSE'
        else:
            raise Exception('期货下单类型错误')

        # 查询持仓
        if offset == 'CLOSE':
            pos = self.positions(code)[code]
            if direction == 'BUY':  # 平空，检查空仓
                if pos.pos_short < amount:
                    # 持仓手数少于要平仓的，修正为持仓数量
                    amount = pos.pos_short

                if 'SHFE' in code or 'INE.sc' in code:
                    if pos.pos_short_his >= amount:
                        offset = 'CLOSE'
                    elif pos.pos_short_today >= amount:
                        offset = 'CLOSETODAY'
                    else:
                        # 持仓不够，返回错误
                        return False
            else:
                if pos.pos_long < amount:
                    # 持仓手数少于要平仓的，修正为持仓数量
                    amount = pos.pos_long

                if 'SHFE' in code or 'INE.sc' in code:
                    if pos.pos_long_his >= amount:
                        offset = 'CLOSE'
                    elif pos.pos_long_today >= amount:
                        offset = 'CLOSETODAY'
                    else:
                        # 持仓不够，返回错误
                        return False

        order = None

        try_nums = 0
        amount_left = amount
        while amount_left > 0:
            try:
                quote = self.get_api().get_quote(code)
                price = quote.ask_price1 if direction == 'BUY' else quote.bid_price1
                if price is None:
                    continue
                order = self.get_api().insert_order(code,
                                                    direction=direction,
                                                    offset=offset,
                                                    volume=int(amount_left),
                                                    limit_price=price,
                                                    )
                time.sleep(2)
                if order.status == 'ALIVE':
                    # 取消订单，未成交的部分继续挂单
                    self.cancel_order(order)
                if order.is_error:
                    print(f'{code} {o_type}下单失败，原因：{order.last_msg}')
                    return False
                amount_left = order.volume_left
            except Exception as e:
                print(f'下单异常 {e} 重试')
                try_nums += 1
                if try_nums >= 8:
                    return False

        if order is None:
            return False

        return {'id': order.order_id, 'price': order.trade_price, 'amount': amount}

    def all_orders(self):
        """
        获取所有订单 (有效订单)
        """
        raise Exception('不提供查询所有订单的功能')

    def cancel_all_orders(self):
        """
        撤销所有订单
        """
        raise Exception('不提供取消所有订单的功能')

    def cancel_order(self, order: Order):
        """
        取消订单，直到订单取消成功
        """
        while True:
            try:
                self.get_api().cancel_order(order.order_id)
                time.sleep(2)
                if order.status == 'FINISHED' or order.is_dead:
                    break
            except Exception as e:
                print(f'天勤取消订单 {order.order_id} 异常 {e} 重试')

        return None

    def stock_owner_plate(self, code: str):
        raise Exception('交易所不支持')

    def plate_stocks(self, code: str):
        raise Exception('交易所不支持')
