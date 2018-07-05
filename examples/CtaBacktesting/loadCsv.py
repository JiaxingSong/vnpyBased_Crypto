# encoding: UTF-8

"""
导入MC导出的CSV历史数据到MongoDB中
"""

from vnpy.trader.app.ctaStrategy.ctaBase import MINUTE_DB_NAME, POSITION_DB_NAME, DAILY_DB_NAME
from vnpy.trader.app.ctaStrategy.ctaHistoryData import loadVIXHistory, loadMcCsv, loadBTCHistoryCsv, onBarHuobipro, loadUX


if __name__ == '__main__':
    #loadMcCsv('IF0000_1min.csv', MINUTE_DB_NAME, 'IF0000')
    #loadMcCsv('rb0000_1min.csv', MINUTE_DB_NAME, 'rb0000')
    #loadBTCHistoryCsv('USDT_BTC_5min.csv', MINUTE_DB_NAME, 'USDTBTC_5min')
    #loadBTCHistoryCsv('USDT_XRP 5-Minute.csv', MINUTE_DB_NAME, 'xrpusdt')
    loadVIXHistory('VIX.csv', DAILY_DB_NAME,'VIX')
    #loadUX('VIX.csv', DAILY_DB_NAME,'UX')
    #loadBTCHistoryCsv('USDT_XRP 5-Minute.csv', POSITION_DB_NAME, 'KkStraxrpudtegy')
    
    #onBarHuobipro(MINUTE_DB_NAME, 'XRP/USDT')

