from pprint import pprint
import pandas 

def debug(para):
    pprint(vars( para   ))
    
    
def printtable(y):
   if isinstance(y, pandas.core.frame.DataFrame):
    print(y.to_string())
   else:
    print(y)

    
