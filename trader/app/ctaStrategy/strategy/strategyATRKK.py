# encoding: UTF-8

"""
基于King Keltner通道和ATR的交易策略，适合用在股指上，
展示了OCO委托和5分钟K线聚合的方法。

注意事项：作者不对交易盈利做任何保证，策略代码仅供参考
"""

from __future__ import division
import pdb
from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator, 
                                                     ArrayManager)


########################################################################
class KkATRStrategy(CtaTemplate):
    """基于King Keltner通道的交易策略"""
    className = 'KkStrategy'
    author = u'用Python的交易员'

    # 策略参数
    atrLength = 18          # 计算ATR指标的窗口数   
    kkLength = 11           # 计算通道中值的窗口数
    kkDev = 1.6             # 计算通道宽度的偏差
    trailingPrcnt = 10     # 移动止损
    fixedSize = 1           # 每次交易的数量
    maxLength = max(kkLength,atrLength) # 是所有的策略需要的值
    initDays = maxLength        # 初始化数据所用天数和策略最大窗口保持一致

    # 策略变量
    atrValue = 0                        # ATR的值
    kkUp = 0                            # KK通道上轨
    kkDown = 0                          # KK通道下轨
    intraTradeHigh = 0                  # 持仓期内的最高点
    intraTradeLow = 0                   # 持仓期内的最低点

    buyOrderIDList = []                 # OCO委托买入开仓的委托号
    shortOrderIDList = []               # OCO委托卖出开仓的委托号
    orderList = []                      # 保存委托代码的列表

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'kkLength',
                 'kkDev']    

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'kkUp',
               'kkDown']
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos',
                'intraTradeHigh',
                'intraTradeLow']    

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(KkATRStrategy, self).__init__(ctaEngine, setting)
        
        self.bg = BarGenerator(self.onBar, 21, self.onFiveBar)     # 创建K线合成器对象
        self.am = ArrayManager()                    # 改变缓存的最大值，使之与策略所需匹配
        
        self.buyOrderIDList = []
        self.shortOrderIDList = []
        self.orderList = []
        
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' %self.name)
        
        # 载入历史数据，并采用回放计算的方式初始化策略数值
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)

        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）""" 
        self.bg.updateTick(tick)

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        self.bg.updateBar(bar)
    
    #----------------------------------------------------------------------
    def onFiveBar(self, bar):
        """收到5分钟K线"""
        # 撤销之前发出的尚未成交的委托（包括限价单和停止单）
        for orderID in self.orderList:
            self.cancelOrder(orderID)
        self.orderList = []
    
        # 保存K线数据
        am = self.am
        am.updateBar(bar)
        if not am.inited:
            return
        
        # 计算指标数值
        self.kkUp, self.kkDown = am.keltner(self.kkLength, self.kkDev)
        #pdb.set_trace()
        self.atrValue = am.atr(self.atrLength)
        
        size = self.ctaEngine.capital * 0.003 / self.atrValue
        #if size == float("inf") or size == float("-inf"):
        #    self.fixedSize = 0
        #else:
        self.fixedSize = size
        # 判断是否要进行交易
    
        # 当前无仓位，发送OCO开仓委托
        if self.pos == 0 :
            self.intraTradeHigh = bar.high
            self.intraTradeLow = bar.low            
            self.sendOcoOrder(self.kkUp, self.kkDown, self.fixedSize)
    
        # 持有多头仓位
        elif self.pos > 0:
            self.intraTradeHigh = max(self.intraTradeHigh, bar.high)
            self.intraTradeLow = bar.low
            
            l = self.sell(self.intraTradeHigh*(1-self.trailingPrcnt/100), 
                          abs(self.pos), True)
            self.orderList.extend(l)
    
        # 持有空头仓位
        elif self.pos < 0:
            self.intraTradeHigh = bar.high
            self.intraTradeLow = min(self.intraTradeLow, bar.low)
            if(bar.close >= self.intraTradeLow*(1 + self.trailingPrcnt/100)) : 
                l = self.cover(self.intraTradeLow*(1+self.trailingPrcnt/100), abs(self.pos), True)
                self.orderList.extend(l)
            else:
                pass
    
        # 同步数据到数据库
        self.saveSyncData()    
    
        # 发出状态更新事件
        self.putEvent()        

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        if self.pos != 0:
            # 多头开仓成交后，撤消空头委托
            if self.pos > 0:
                for shortOrderID in self.shortOrderIDList:
                    self.cancelOrder(shortOrderID)
            # 反之同样
            elif self.pos < 0:
                for buyOrderID in self.buyOrderIDList:
                    self.cancelOrder(buyOrderID)
            
            # 移除委托号
            for orderID in (self.buyOrderIDList + self.shortOrderIDList):
                if orderID in self.orderList:
                    self.orderList.remove(orderID)
                
        # 发出状态更新事件
        self.putEvent()
        
    #----------------------------------------------------------------------
    def sendOcoOrder(self, buyPrice, shortPrice, volume):
        """
        发送OCO委托
        
        OCO(One Cancel Other)委托：
        1. 主要用于实现区间突破入场
        2. 包含两个方向相反的停止单
        3. 一个方向的停止单成交后会立即撤消另一个方向的
        """
        # 发送双边的停止单委托，并记录委托号
        self.buyOrderIDList = self.buy(buyPrice, volume, True)
        self.shortOrderIDList = self.short(shortPrice, volume, True)
        
        # 将委托号记录到列表中
        self.orderList.extend(self.buyOrderIDList)
        self.orderList.extend(self.shortOrderIDList)

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass