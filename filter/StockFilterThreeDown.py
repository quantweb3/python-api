#!/usr/bin/python3
import os
import json
import datetime
import jsonpickle
import numpy as np
from filter.StockFilter import StockFilter

 

class StockFilterThreeDown(StockFilter):
     
    def __init__(self,config):
        StockFilter.__init__(self,config)
        
    def getHistory(self):
        self.history=[]
        sql = "SELECT * FROM stockhistory WHERE ts_code='"+ self.tscode+"'  order by tradedate"
        cursor = self.db.cursor()
        cursor.execute(sql)  
        self.history = cursor.fetchall() 
    
    
    ##  三低类的检查方法
    def filterOne(self):
        if (len(self.history)<3):
            return  {"passed":False};
        
        if (  self.history[-1]["close"] <self.history[-1]["open"]
              and   self.history[-2]["close"]< self.history[-2]["open"] 
              and   self.history[-3]["close"] < self.history[-3]["open"]
              and   not  'ST' in  self.name
           ):
           
           record={};
           record['name']=self.name
           record['executedate'] = datetime.datetime.now().strftime('%Y-%m-%d')
           record['ts_code']=self.tscode
           record['close_1']=self.history[-1]["close"] 
           record['close_2']=self.history[-2]["close"] 
           record['close_3']=self.history[-3]["close"] 
           record['close_4']=self.history[-4]["close"] 
           
           ## 计算振幅
           amplitude_last=  100* abs(self.history[-1]["high"] - self.history[-1]["low"]) / self.history[-2]["close"]
           record['amplitude_last']= float(np.round(amplitude_last, 2))
           return {"passed":True,"record":record};
        else:
           return {"passed":False};
        
            
    def saveFilterResult(self) :
        cursor = self.db.cursor()
        
        cursor.execute("delete from filterresult_threelow " )  
        for mydict in self.filterResults:
            placeholders = ', '.join(['%s'] * len(mydict))
            columns = ', '.join("`" + str(x).replace('/', '_') + "`" for x in mydict.keys())
            values = ', '.join("'" + str(x).replace('/', '_') + "'" for x in mydict.values())
            sql = "INSERT INTO %s ( %s ) VALUES ( %s );" % ('filterresult_threelow', columns, values)
            cursor.execute(sql)  
        self.db.close()
        

        for (index, item) in enumerate(self.filterResults):
            item['serial'] = index + 1
    
            
        
        
        