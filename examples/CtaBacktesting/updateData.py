# encoding: UTF-8

"""
导入MC导出的CSV历史数据到MongoDB中
"""

from vnpy.trader.app.ctaStrategy.ctaBase import MINUTE_DB_NAME
from vnpy.trader.app.ctaStrategy.ctaHistoryData import loadMcCsv, loadBTCHistoryCsv, onBarHuobipro
from apscheduler.schedulers.background import BackgroundScheduler
import time

if __name__ == '__main__':
    sched = BackgroundScheduler()
    sched.add_job(lambda: onBarHuobipro(MINUTE_DB_NAME, 'XRP/USDT'), 'interval', minutes=1, id='download_ohlcv')
    print('schedual start')
    sched.start()

    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
            # Not strictly necessary if daemonic mode is enabled but should be done if possible
            scheduler.shutdown()    

