from pprint import pprint
import pandas 
from colorama import Fore, Back, Style


def debug(para):
    paraType=type(para)
    if paraType==dict:
       pprint(vars( para   ))
    if paraType==list:
       pprint( para)
    
    
def printtable(y):
   if isinstance(y, pandas.core.frame.DataFrame):
    print(Fore.RED + '---------------------------------------------------------------------')
    # print first 10 lines
    print(y.head(10).to_string())  
   #  print(y.to_string())
    print(Fore.RED + '---------------------------------------------------------------------')
    print(Style.RESET_ALL)
    
   else:
    print(y)
    

def printMoney():
    
            
    # print(Fore.RED + '>>>>>>>>>>')
    # print('当前可用资金', cerebro.broker.getcash())
    # # print('当前总资产', cerebro.broker.getvalue())
    # # print('当前持仓量', cerebro.broker.getposition(cerebro.data).size)
    # # print('当前持仓成本', cerebro.broker.getposition(cerebro.data).price)
    # print(Fore.RED + '*****************8')
    # print(Style.RESET_ALL)   
    print("^^^^^^^^^^")

    
