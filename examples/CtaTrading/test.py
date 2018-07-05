from vnpy.trader.gateway import huobiproGateway
from vnpy.api.huobi import TradeApi, DataApi
from vnpy.event import EventEngine2
from vnpy.trader.vtGateway import *
from vnpy.trader.vtFunction import getJsonPath, getTempPath
import pdb
import pymongo
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
from vnpy.trader.vtGlobal import globalSetting

class myDataApi(DataApi):
    def __init__(self, gateway):
        """Constructor"""
        super(myDataApi, self).__init__()
        self.gateway = gateway                  
        self.gatewayName = gateway.gatewayName  
        self.connectionStatus = False        
        self.tickDict = {}
        self.subscribeDict = {}

    def connect(self, exchange, proxyHost, proxyPort):
        if exchange == 'huobi':
            url = "wss://api.huobi.pro/ws"
        else:
            url = "wss://api.hadax.com/ws"
        if proxyHost:
            self.connectionStatus = super(myDataApi, self).connect(url, proxyHost, proxyPort)
        else:
            self.connectionStatus = super(myDataApi, self).connect(url)
        self.gateway.mdConnected = True
        if self.connectionStatus:
            print(u'Connected to market data server successfully')
            for req in self.subscribeDict.values():
                self.subscribe(req)
    
    #----------------------------------------------------------------------
    def onMarketDetail(self, data):
        symbol = data['ch'].split('.')[1]
        
        tick = self.tickDict.get(symbol, None)
        if not tick:
            return     
        
        tick.datetime = datetime.fromtimestamp(data['ts']/1000)
        tick.date = tick.datetime.strftime('%Y%m%d')
        tick.time = tick.datetime.strftime('%H:%M:%S.%f')
        
        t = data['tick']
        tick.openPrice = t['open']
        tick.highPrice = t['high']
        tick.lowPrice = t['low']
        tick.lastPrice = t['close']
        tick.volume = t['vol']
        tick.preClosePrice = tick.openPrice
        
        if tick.bidPrice1:
            newtick = copy(tick)
            self.gateway.onTick(tick)

#--------------------------------------------------------

ee = EventEngine2()
huobiGW = huobiproGateway.HuobiGateway(ee)

huobiGW.connect()
#myApi.subscribeMarketDetail('xrpusdt')

api = DataApi()
api.connect("wss://api.huobi.pro/ws")
#api.subscribeMarketDetail('xrpusdt')
req = {
  "req": "market.xrpusdt.kline.1day",
  "id": "id01"    
}
client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
collection = client['VnTrader_1day']['xrpusdt']
pdb.set_trace()

huobiGW.dataApi.sendReq(req)
#api.sendReq(req)
