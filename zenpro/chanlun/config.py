"""
服务总配置文件
"""

# WEB 服务器IP
WEB_HOST = '127.0.0.1'

# WEB 登录密码，为空则无需进行登录
LOGIN_PWD = 'cl123456'

# 代理服务器配置
PROXY_HOST = '127.0.0.1'
PROXY_PORT = '7890'

# 数据库配置 h103.151.148.2 -pcnix@123456
DB_HOST = '103.151.148.2'
DB_PORT = 3306
DB_USER = 'mysqlx'
DB_PWD = 'cnix@123456'
DB_DATABASE = 'chanlun_klines'

# Redis 配置
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379

# 各个市场的交易所设置（只适用于WEB页面的行情展示）
EXCHANGE_A = 'tdx'
EXCHANGE_HK = 'futu'
EXCHANGE_FUTURES = 'tq'
EXCHANGE_CURRENCY = 'binance'
EXCHANGE_US = 'polygon'

# 富途API配置（不使用请将 FUTU_HOST 留空）
FUTU_HOST = '127.0.0.1'
FUTU_PORT = 11111
FUTU_UNLOCK_PWD = ''

# 天勤账号配置
TQ_USER = ''
TQ_PWD = ''
TQ_SP_NAME = 'simnow'
TQ_SP_ACCOUNT = ''
TQ_SP_PWD = ''

# 币安交易所配置
BINANCE_APIKEY = ''
BINANCE_SECRET = ''

# ZB交易所配置
ZB_APIKEY = ''
ZB_SECRET = ''

# 美股 Ploygon API 配置（申请网址 https://polygon.io/）
POLYGON_APIKEY = ''

# 美股 Alpaca API 配置（申请网址 https://alpaca.markets/）
ALPACA_APIKEY = ''
ALPACA_SECRET = ''

# 钉钉消息配置
DINGDING_KEY_A = {'token': '', 'secret': ''}
DINGDING_KEY_HK = {'token': '', 'secret': ''}
DINGDING_KEY_US = {'token': '', 'secret': ''}
DINGDING_KEY_CURRENCY = {'token': '', 'secret': ''}
DINGDING_KEY_FUTURES = {'token': '', 'secret': ''}

# 七牛云配置 (用于消息推送时的图片保存)
QINIU_AK = ''
QINIU_SK = ''
QINIU_BUCKET_NAME = ''
QINIU_PATH = ''
QINIU_URL = 'http://**'

# 自选组配置
STOCK_ZX = [{'name': '我的持仓', 'short_name': '持'}, {'name': '今日关注', 'short_name': '今'}]
HK_ZX = [{'name': '我的持仓', 'short_name': '持'}, {'name': '今日关注', 'short_name': '今'}]
FUTURES_ZX = [{'name': '我的持仓', 'short_name': '持'}, {'name': '今日关注', 'short_name': '今'}]
CURRENCY_ZX = [{'name': '我的持仓', 'short_name': '持'}, {'name': '今日关注', 'short_name': '今'}]
US_ZX = [{'name': '我的持仓', 'short_name': '持'}, {'name': '今日关注', 'short_name': '今'}]

"""
缠论其他相关设置
"""

# 是否开启低级别数据转高级别图表展示功能
# 高级别对应的低级别对照关系在 cl_utils.py kcharts_to_new_frequency 方法中，可自行按需求更改
# 因为数据服务提供差异，级别不要设置太小，太小转高级别就没有多少数据了
# 其中的对应关系倍数也不固定，基本在 3-8 区间内，也会因为数据提供API限制不会找到符合要求的低级别周期
# 低级别转高级别方法在 chanlun.exchange.exchange.py convert_***_kline_frequency，也需要有对应的周期转换配置
# 自己根据实际情况，根据经验自行设置
enable_kchart_low_to_high = False

# 段内中枢超过几段进行拆分（单数，最小 9，包括中枢连接段）
xd_zs_max_lines_split = 11
# 特殊情况，拆分线段时，是否允许单笔成段
allow_split_one_line_to_xd = True

# 笔分型是否严格处理
# False : 不严格处理，允许顶的最低点低于底分型最低点，允许底分型的最高点高于顶分型的最高点
# True：严格处理，不允许顶的最低点低于底分型最低点，不允许底分型的最高点高于顶分型的最高点
allow_bi_fx_strict = True
