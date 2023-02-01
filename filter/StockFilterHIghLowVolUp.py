#!/usr/bin/python3
import os
from sqlalchemy import false
import json
import datetime
import jsonpickle
import numpy as np
from filter.StockFilter import StockFilter

 

class StockFilterHIghLowVolUp(StockFilter):
     
    def __init__(self,config):
        StockFilter.__init__(self,config)
        self.limitUpRateSH=1.1  ##6xxxx 上海
        self.limitUpRateSZ=1.1  ##00xxxx 3XXXX 深圳
        self.NextDayVolumeFactor =float(config.get('NextDayVolumeFactor'))
        self.startDate=config.get('startDate')   
        self.endDate= config.get('endDate')   
        
        
    def getHistory(self):
        self.history=[]
        sql = "SELECT * FROM stockhistory WHERE ts_code='"+ self.tscode+"'   and tradedate between  '"+self.startDate +"' and '"+ self.endDate +"' order by tradedate"
        cursor = self.db.cursor()
        cursor.execute(sql)  
        self.history = cursor.fetchall() 
    
    
    ##  高开低走巨阴的检查方法
    def filterOne(self):
        
        rate=1.1
        if 'SH' in self.tscode:
            rate=self.limitUpRateSH
        
        if 'SZ' in self.tscode:
            rate=self.limitUpRateSZ
    
        if (len(self.history)<=2):
            self.checkPass=False
            print(self.tscode+'数据不足')
            return  {"passed":False};
            
        
        index =1  
        while index < len(self.history) -1 :
            pre_index =index-1
            next_index=index+1
            
            
            if (self.history[index]["close"] > self.history[pre_index]["close"]* rate #这一天(index)涨停,涨停的定位是今日股价比上次涨10%
                and self.history[next_index]["open"]>self.history[index]["close"]      #后一天(next_index)高开
                and self.history[next_index]["close"]<self.history[next_index]["open"] # 后一天(next_index)低走
                and self.history[next_index]["volume"]>self.history[index]["volume"]*self.NextDayVolumeFactor # 后一天交易量是前一天的NextDayVolumeFactor倍数
                
                ):
                    record=self.history[index]
                    record['executedate'] = datetime.datetime.now().strftime('%Y-%m-%d')
                    record['name']=self.name
                    record['next_tradedate']=self.history[next_index]["tradedate"]
                    record['next_open']=self.history[next_index]["open"]
                    record['next_close']=self.history[next_index]["close"]
                    record['next_volume']=self.history[next_index]["volume"]
                    record['next_high']=self.history[next_index]["high"]
                    return {"passed":True,"record":record};
                    
            index=index+1
        return  {"passed":False };

        
            
    def saveFilterResult(self) :
        
        cursor = self.db.cursor()
        cursor.execute("delete from filterresult_highlow " )  
        for mydict in self.filterResults:
            placeholders = ', '.join(['%s'] * len(mydict))
            columns = ', '.join("`" + str(x).replace('/', '_') + "`" for x in mydict.keys())
            values = ', '.join("'" + str(x).replace('/', '_') + "'" for x in mydict.values())
            sql = "INSERT INTO %s ( %s ) VALUES ( %s );" % ('filterresult_highlow', columns, values)
            print(sql)
            cursor.execute(sql)  
        self.db.close()

        for (index, item) in enumerate(self.filterResults):
            item['serial'] = index + 1
    
            
        
        
        