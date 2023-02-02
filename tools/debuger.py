from pprint import pprint
import pandas 
from colorama import Fore, Back, Style


def debug(para):
    pprint(vars( para   ))
    
    
def printtable(y):
   if isinstance(y, pandas.core.frame.DataFrame):
    
    
    print(Fore.RED + '---------------------------------------------------------------------')
    print(y.to_string())
    print(Fore.RED + '---------------------------------------------------------------------')
    print(Style.RESET_ALL)
    
   else:
    print(y)

    
