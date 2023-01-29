#!/usr/bin/python3
import os
import datetime
import jsonpickle
from tools.functions import getDbConn
 

class StockFilter():
    
    def __init__(self,config):
        print('初始化 StockFilter')
        self.db=getDbConn()
        self.config=config
        self.allcodes=[]
        self.getAllCodes()
        self.filterResults=[]

        ## tscode,name ,history 是针对某一个股票的运行时变量
        self.tscode=None
        self.name=None
        self.history=[]

   
    def getAllCodes(self):
        sql = " SELECT ts_code,name FROM codes     " 
        cursor = self.db.cursor()
        cursor.execute(sql)  
        cs=cursor.fetchall()
        self.allcodes=cs
        return self
        
    
    # 需要重载的方法    
    def getHistory(self):
        pass
        
        
    # 需要重载的方法     
    def saveFilterResult(self):
        pass      
        
    
    # 需要重载的方法 
    def filterOne(self):
        pass
    
    
    def filterAll(self):
            
        for i,val in enumerate(self.allcodes):
            self.tscode=val['ts_code']
            self.name=val['name']
            print("检查"+self.name)
            self.getHistory()
            _tmp=self.filterOne() 
             
            if  (_tmp['passed']):
                self.filterResults.append( _tmp['record'] ) 
                
        return self
        
    def debug(self):
        print("debug")
        json = jsonpickle.encode(self.filterResults,unpicklable=False)
        print(json)
        return self;   
    