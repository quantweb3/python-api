#!/usr/bin/python3
import os
import json
import datetime
import jsonpickle
import numpy as np
from filter.StockFilter import StockFilter

 

class StockFilter213(StockFilter):
     
    def __init__(self,config):
        StockFilter.__init__(self,config)
        
    def getHistory(self):
        self.history=[]
        sql = "SELECT * FROM stockhistory WHERE ts_code='"+ self.tscode+"'  order by tradedate"
        cursor = self.db.cursor()
        cursor.execute(sql)  
        self.history = cursor.fetchall() 
    
    
    ##  213 
    def filterOne(self):
        if (len(self.history)<3):
            return  {"passed":False};
        
        if (        self.history[-1]["close"] > self.history[-1]["open"]
              and   self.history[-2]["close"] > self.history[-2]["open"]
              and   self.history[-3]["close"] > self.history[-3]["open"]
              and   self.history[-1]["volume"] > self.history[-2]["volume"]
              and   self.history[-1]["volume"] > self.history[-3]["volume"]
              and   self.history[-3]["volume"] > self.history[-2]["volume"]
              and   self.history[-1]["volume"] > 2*self.history[-2]["volume"]
              and   not  'ST' in  self.name
           ):
           
           record={};
           record['name']=self.name
           record['executedate'] = datetime.datetime.now().strftime('%Y-%m-%d')
           record['ts_code']=self.tscode
           record['close_1']=self.history[-1]["close"] 
           record['close_2']=self.history[-2]["close"] 
           record['close_3']=self.history[-3]["close"] 
           record['volume_1']=self.history[-1]["volume"] 
           record['volume_2']=self.history[-2]["volume"] 
           record['volume_3']=self.history[-3]["volume"] 
           
           return {"passed":True,"record":record};
        else:
           return {"passed":False};
        
            
    def saveFilterResult(self) :
        cursor = self.db.cursor()
        
        cursor.execute("delete from filterresult_213 " )  
        for mydict in self.filterResults:
            placeholders = ', '.join(['%s'] * len(mydict))
            columns = ', '.join("`" + str(x).replace('/', '_') + "`" for x in mydict.keys())
            values = ', '.join("'" + str(x).replace('/', '_') + "'" for x in mydict.values())
            sql = "INSERT INTO %s ( %s ) VALUES ( %s );" % ('filterresult_213', columns, values)
            cursor.execute(sql)  
        self.db.close()
        

        for (index, item) in enumerate(self.filterResults):
            item['serial'] = index + 1
    
            
        
        
        