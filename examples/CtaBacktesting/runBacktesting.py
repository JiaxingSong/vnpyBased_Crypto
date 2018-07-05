# encoding: UTF-8

"""
展示如何执行策略回测。
"""

from __future__ import division


from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME, DAILY_DB_NAME


if __name__ == '__main__':
    from vnpy.trader.app.ctaStrategy.strategy.strategyATRKK import KkATRStrategy
    from vnpy.trader.app.ctaStrategy.strategy.strategyAtrRsi import AtrRsiStrategy
    
    # 创建回测引擎
    engine = BacktestingEngine()
    
    
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)

    # 设置回测用的数据起始日期
    engine.setStartDate('20130601')
    
    # 设置产品相关参数
    engine.setSlippage(0.01)     # 股指1跳
    engine.setRate(1/1000)   # 万0.3
    engine.setSize(1)         # 股指合约大小 
    engine.setPriceTick(0.001)    # 股指最小价格变动
    
    # 设置使用的历史数据库
    engine.setDatabase(DAILY_DB_NAME, 'VIXY')
    
    # 在引擎中创建策略对象
    d = {}
    engine.initStrategy(KkATRStrategy, d)
    
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果
    engine.showBacktestingResult()