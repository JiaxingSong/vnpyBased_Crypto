# encoding: UTF-8

"""
本模块中主要包含：
1. 将MultiCharts导出的历史数据载入到MongoDB中用的函数
2. 将通达信导出的历史数据载入到MongoDB中的函数
3. 将交易开拓者导出的历史数据载入到MongoDB中的函数
4. 将OKEX下载的历史数据载入到MongoDB中的函数
"""

import csv
from datetime import datetime, timedelta
from time import time

import pymongo

from vnpy.trader.vtGlobal import globalSetting
from vnpy.trader.vtConstant import *
from vnpy.trader.vtObject import VtBarData
from .ctaBase import SETTING_DB_NAME, TICK_DB_NAME, MINUTE_DB_NAME, DAILY_DB_NAME
import ccxt


#----------------------------------------------------------------------
def downloadEquityDailyBarts(self, symbol):
    """
    下载股票的日行情，symbol是股票代码
    """
    print u'开始下载%s日行情' %symbol
    
    # 查询数据库中已有数据的最后日期
    cl = self.dbClient[DAILY_DB_NAME][symbol]
    cx = cl.find(sort=[('datetime', pymongo.DESCENDING)])
    if cx.count():
        last = cx[0]
    else:
        last = ''
    # 开始下载数据
    import tushare as ts
    
    if last:
        start = last['date'][:4]+'-'+last['date'][4:6]+'-'+last['date'][6:]
        
    data = ts.get_k_data(symbol,start)
    
    if not data.empty:
        # 创建datetime索引
        self.dbClient[DAILY_DB_NAME][symbol].ensure_index([('datetime', pymongo.ASCENDING)], 
                                                            unique=True)                
        
        for index, d in data.iterrows():
            bar = VtBarData()
            bar.vtSymbol = symbol
            bar.symbol = symbol
            try:
                bar.open = d.get('open')
                bar.high = d.get('high')
                bar.low = d.get('low')
                bar.close = d.get('close')
                bar.date = d.get('date').replace('-', '')
                bar.time = ''
                bar.datetime = datetime.strptime(bar.date, '%Y%m%d')
                bar.volume = d.get('volume')
            except KeyError:
                print d
            
            flt = {'datetime': bar.datetime}
            self.dbClient[DAILY_DB_NAME][symbol].update_one(flt, {'$set':bar.__dict__}, upsert=True)            
        
        print u'%s下载完成' %symbol
    else:
        print u'找不到合约%s' %symbol

#----------------------------------------------------------------------
def loadMcCsv(fileName, dbName, symbol):
    """将Multicharts导出的csv格式的历史数据插入到Mongo数据库中"""
    import csv
    
    start = time()
    print u'开始读取CSV文件%s中的数据插入到%s的%s中' %(fileName, dbName, symbol)
    
    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort']) 
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)   
    
    # 读取数据和插入到数据库
    reader = csv.DictReader(file(fileName, 'r'))
    for d in reader:
        bar = VtBarData()
        bar.vtSymbol = symbol
        bar.symbol = symbol
        bar.open = float(d['Open'])
        bar.high = float(d['High'])
        bar.low = float(d['Low'])
        bar.close = float(d['Close'])
        bar.date = datetime.strptime(d['Date'], '%Y-%m-%d').strftime('%Y%m%d')
        bar.time = d['Time']
        bar.datetime = datetime.strptime(bar.date + ' ' + bar.time, '%Y%m%d %H:%M:%S')
        bar.volume = d['TotalVolume']

        flt = {'datetime': bar.datetime}
        collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)  
        print bar.date, bar.time
    
    print u'插入完毕，耗时：%s' % (time()-start)

#----------------------------------------------------------------------
def loadTbCsv(fileName, dbName, symbol):
    """将TradeBlazer导出的csv格式的历史分钟数据插入到Mongo数据库中"""
    import csv
    
    start = time()
    print u'开始读取CSV文件%s中的数据插入到%s的%s中' %(fileName, dbName, symbol)
    
    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)   
    
    # 读取数据和插入到数据库
    reader = csv.reader(file(fileName, 'r'))
    for d in reader:
        bar = VtBarData()
        bar.vtSymbol = symbol
        bar.symbol = symbol
        bar.open = float(d[1])
        bar.high = float(d[2])
        bar.low = float(d[3])
        bar.close = float(d[4])
        bar.date = datetime.strptime(d[0].split(' ')[0], '%Y/%m/%d').strftime('%Y%m%d')
        bar.time = d[0].split(' ')[1]+":00"
        bar.datetime = datetime.strptime(bar.date + ' ' + bar.time, '%Y%m%d %H:%M:%S')
        bar.volume = d[5]
        bar.openInterest = d[6]

        flt = {'datetime': bar.datetime}
        collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)  
        print bar.date, bar.time
    
    print u'插入完毕，耗时：%s' % (time()-start)
    
 #----------------------------------------------------------------------
def loadTbPlusCsv(fileName, dbName, symbol):
    """将TB极速版导出的csv格式的历史分钟数据插入到Mongo数据库中"""
    import csv    

    start = time()
    print u'开始读取CSV文件%s中的数据插入到%s的%s中' %(fileName, dbName, symbol) 

    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)      

    # 读取数据和插入到数据库
    reader = csv.reader(file(fileName, 'r'))
    for d in reader:
        bar = VtBarData()
        bar.vtSymbol = symbol
        bar.symbol = symbol
        bar.open = float(d[2])
        bar.high = float(d[3])
        bar.low = float(d[4])
        bar.close = float(d[5])
        bar.date = str(d[0])
        
        tempstr=str(round(float(d[1])*10000)).split(".")[0].zfill(4)
        bar.time = tempstr[:2]+":"+tempstr[2:4]+":00"
        
        bar.datetime = datetime.strptime(bar.date + ' ' + bar.time, '%Y%m%d %H:%M:%S')
        bar.volume = d[6]
        bar.openInterest = d[7]
        flt = {'datetime': bar.datetime}
        collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)  
        print bar.date, bar.time    

    print u'插入完毕，耗时：%s' % (time()-start)

#----------------------------------------------------------------------
def loadTdxCsv(fileName, dbName, symbol):
    """将通达信导出的csv格式的历史分钟数据插入到Mongo数据库中"""
    import csv
    
    start = time()
    print u'开始读取CSV文件%s中的数据插入到%s的%s中' %(fileName, dbName, symbol)
    
    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)   
    
    # 读取数据和插入到数据库
    reader = csv.reader(file(fileName, 'r'))
    for d in reader:
        bar = VtBarData()
        bar.vtSymbol = symbol
        bar.symbol = symbol
        bar.open = float(d[2])
        bar.high = float(d[3])
        bar.low = float(d[4])
        bar.close = float(d[5])
        bar.date = datetime.strptime(d[0], '%Y/%m/%d').strftime('%Y%m%d')
        bar.time = d[1][:2]+':'+d[1][2:4]+':00'
        bar.datetime = datetime.strptime(bar.date + ' ' + bar.time, '%Y%m%d %H:%M:%S')
        bar.volume = d[6]
        bar.openInterest = d[7]

        flt = {'datetime': bar.datetime}
        collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)  
        print bar.date, bar.time
    
    print u'插入完毕，耗时：%s' % (time()-start)

#----------------------------------------------------------------------
def loadOKEXCsv(fileName, dbName, symbol):
    """将OKEX导出的csv格式的历史分钟数据插入到Mongo数据库中"""
    start = time()
    print u'开始读取CSV文件%s中的数据插入到%s的%s中' %(fileName, dbName, symbol)

    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)

    # 读取数据和插入到数据库
    reader = csv.reader(open(fileName,"r"))
    for d in reader:
        if len(d[1]) > 10:
            bar = VtBarData()
            bar.vtSymbol = symbol
            bar.symbol = symbol

            bar.datetime = datetime.strptime(d[1], '%Y-%m-%d %H:%M:%S')
            bar.date = bar.datetime.date().strftime('%Y%m%d')
            bar.time = bar.datetime.time().strftime('%H:%M:%S')

            bar.open = float(d[2])
            bar.high = float(d[3])
            bar.low = float(d[4])
            bar.close = float(d[5])

            bar.volume = float(d[6])
            bar.tobtcvolume = float(d[7])

            flt = {'datetime': bar.datetime}
            collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)
            print('%s \t %s' % (bar.date, bar.time))

    print u'插入完毕，耗时：%s' % (time()-start)
    
def loadBTCHistoryCsv(fileName, dbName, symbol):
    """将BTC导出的csv格式的历史30分钟数据插入到Mongo数据库中"""
    start = time()
    print u'开始读取CSV文件%s中的数据插入到%s的%s中' %(fileName, dbName, symbol)

    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)

    #pdb.set_trace()
    # 读取数据和插入到数据库
    reader = csv.reader(open(fileName,"r"))
    date = 0 
    for d in reader:
        if len(d[0]) >= 10:
            bar = VtBarData()
            bar.vtSymbol = 'xrpusdt'
            bar.symbol = symbol
            bar.datetime = datetime.fromtimestamp(int(d[0]))
            bar.date, bar.time = bar.datetime.strftime('%Y-%m-%d %H:%M:%S').split(' ')

            bar.high = float(d[1])
            bar.low = float(d[2])
            bar.open = float(d[3])
            bar.close = float(d[4])

            bar.volume = float(d[5])
            bar.tobtcvolume = float(d[6])
            bar.weightedAvg = float(d[7])

            flt = {'datetime': bar.datetime}
            collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)
            year,month,day = bar.date.split('-') 
            if day != date:
              print('%s \t %s' % (bar.date, bar.time))
              date = day
    print u'插入完毕，耗时：%s' % (time()-start)

def onBarHuobipro(dbName, symbol, timeframe='1m'):
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)
    houbipro = ccxt.huobipro()
    ohlcv = houbipro.fetch_ohlcv(symbol,timeframe,time(),1)
    bar = VtBarData()
    bar.vtSymbol = symbol
    bar.symbol = symbol
    bar.datetime = datetime.fromtimestamp(ohlcv[0][0]/1000)
    bar.date, bar.time = bar.datetime.strftime('%Y-%m-%d %H:%M:%S').split(' ')        
    bar.high = float(ohlcv[0][1])
    bar.low = float(ohlcv[0][2])
    bar.open = float(ohlcv[0][3])
    bar.close = float(ohlcv[0][4])
    bar.volume = float(ohlcv[0][5])
    flt = {'datetime': bar.datetime}
    collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)

def loadVIXHistory(fileName, dbName, symbol):
    """将VIX导出的csv格式的历史日线数据插入到Mongo数据库中"""
    start = time()
    print u'开始读取VIX CSV文件%s中的数据插入到%s的%s中' %(fileName, dbName, symbol)

    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection= client[dbName]['VIXY']
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)

    #pdb.set_trace()
    # 读取数据和插入到数据库
    reader = csv.reader(open(fileName,"r"), dialect=csv.excel_tab)
    #read in VIXY
    for d in reader:
        bar = VtBarData()
        bar.vtSymbol = 'VIXY'
        bar.symbol = symbol
        context = d[0].split(',')
        if context[4]=='':
            break
        year,month,day = context[4].split('/')
        bar.datetime = datetime(int(year), int(month), int(day), 9, 15, 15)
        bar.price = float(context[5])
        bar.open = bar.price
        bar.high = bar.price
        bar.low = bar.price
        bar.close = bar.price
        bar.volume = float(context[6])
        bar.smavg = 0 if context[7]=='' else float(context[7]) 
        
        flt = {'datetime': bar.datetime}
        collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)
        print('%s' % (bar.datetime))
    print u'插入完毕，耗时：%s' % (time()-start)

def loadUX(fileName, dbName, symbol):
    """将VIX导出的csv格式的历史日线数据插入到Mongo数据库中"""
    start = time()
    print u'开始读取VIX CSV文件%s中的数据插入到%s的%s中' %(fileName, dbName, symbol)

    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection= client[dbName]['UX']
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)

    reader = csv.reader(open(fileName,"r"), dialect=csv.excel_tab)
    #read in VIXY
    for d in reader:
        bar = VtBarData()
        bar.vtSymbol = 'UX'
        bar.symbol = symbol
        context = d[0].split(',')
        if context[0]=='':
            break
        year,month,day = context[0].split('/')
        bar.datetime = datetime(int(year), int(month), int(day), 9, 15, 15)
        bar.ux1 = float(context[1])
        bar.ux2 = float(context[2])
        bar.ux3 = 0 if context[3]=='' else float(context[3]) 
        
        flt = {'datetime': bar.datetime}
        collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)
        print('%s' % (bar.datetime))
    print u'插入完毕，耗时：%s' % (time()-start)