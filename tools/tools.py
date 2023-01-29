import os
import sys
import tushare as ts
import pandas as pd
import pymysql
from datetime import datetime, time
from  functions import getDbConn,getTushareToken
import platform



pro = ts.pro_api(getTushareToken())

df = pro.query('trade_cal', exchange='SSE', start_date='20200101', end_date='20220220', fields='exchange,cal_date,is_open,pretrade_date', is_open='1')

print(df)



# 000001.SZ