# 从未来导入绝对导入，除法，打印功能，unicode_literals
from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import pandas as pd
from datetime import datetime
from colorama import Fore, Back, Style
import sys
from pprint import pprint
from indicators.indicator_goodday import *
sys.path.append("..")
from tools.debuger import *
from indicators.mytrix import MyTrix

class NoStrategy(bt.Strategy):
    params = (('trixperiod', 15),)

    def __init__(self):
        MyTrix(self.data, period=self.p.trixperiod) 
 