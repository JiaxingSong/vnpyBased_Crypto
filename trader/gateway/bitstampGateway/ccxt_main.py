import pdb
import ccxt
#import asyncio
import time
from apscheduler.schedulers.background import BackgroundScheduler
from multiprocessing import Pool
from ccxt_market_data import ccxtMarketData
from ccxt_market_data import OHLCV
from ccxt_market_data import TICKER

market_data = ccxtMarketData()

#init all exchanges
def init_exchanges():
  exchanges = ccxt.exchanges
  objs = []
  for ex in exchanges:
    ex_obj = eval('ccxt.'+ex+'()')
    objs.append(ex_obj)
  return objs

#init exchanges with ohlcv data.(open,high,low,close,volume)
def init_ohlcv_exchanges():
  exchanges=['acx', 'allcoin', 'binance', 'bittrex', 
             'btcturk', 'cex', 'gdax', 'kraken',
             'okcoinusd', 'okex', 'zb']
  objs = []
  for ex in exchanges:
    ex_obj = eval('ccxt.'+ex+'()')
    objs.append(ex_obj)
  return objs

#init the exchanges that allows us to access market data without secret&keys
def init_market_public_exchanges():
  exchanges=['_1btcxe', 'acx', 'allcoin', 'anxpro', 'binance', 'bit2c', 'bitbay', 'bitcoincoid', 
             'bitfinex', 'bitfinex2', 'bitflyer', 'bithumb', 'bitlish', 'bitmarket', 'bitmex', 
             'bitso', 'bitstamp', 'bitstamp1', 'bittrex', 'bl3p', 'bleutrade', 'braziliex', 'btcbox', 
             'btcchina', 'btcexchange', 'btcmarkets', 'btctradeua', 'btcturk', 'btcx', 'bxinth', 'ccex', 
             'cex', 'chbtc', 'chilebit', 'coincheck', 'coinexchange', 'coinfloor', 'coingi', 
             'coinmarketcap', 'coinmate', 'coinsecure', 'coinspot', 'cryptopia', 'dsx', 'exmo', 'foxbit',
             'fybse', 'fybsg', 'gatecoin', 'gateio', 'gdax', 'gemini', 'getbtc', 'hitbtc', 'hitbtc2', 
             'huobi', 'huobicny', 'huobipro', 'independentreserve', 'itbit', 'jubi', 'kraken', 
             'kucoin', 'kuna', 'lakebtc', 'liqui', 'livecoin', 'luno', 'lykke', 'mercado', 'mixcoins', 
             'nova', 'okcoincny', 'okcoinusd', 'okex', 'paymium', 'poloniex', 'qryptos', 'quadrigacx', 
             'quoinex', 'southxchange', 'surbitcoin', 'therock', 'tidex', 'urdubit', 'vaultoro', 
             'vbtc', 'virwox', 'wex', 'zaif', 'zb']
  objs = []
  for ex in exchanges:
    ex_obj = eval('ccxt.'+ex+'()')
    objs.append(ex_obj)
  return objs



def download_data(exchanges):
  for exchange in exchanges:
    exchange.load_markets()
    symbols = list(exchange.markets.keys())
    for symbol in symbols:
      #symbol = 'ETH/BTC'
      ticker = exchange.fetchTicker(symbol)
      order_book = exchange.fetch_order_book(symbol,{'depth':5})
      trades = exchange.fetch_trades(symbol)
      OHLCV = None
      if exchange.hasFetchOHLCV:
        OHLCV = exchange.fetch_ohlcv(symbol,'1d')
      market_data.save_data(exchange,symbol,ticker,order_book,trades,OHLCV)

def load_markets(exchange):
  times = 3
  while times > 0 :
    try:
      exchange.load_markets(True)
    except Exception as e:
      times = times - 1
    else:
      break
  if exchange.markets==None:
    return []
  return list(exchange.markets.keys())


#download ohlcv data from input exchanges
def download_ohlcv(exchanges):
  for ex in exchanges:
    #symbols = load_markets(ex)
    #if not symbols:
    #  print('Error: market data of '+ex.id+' cannot be reloaded')
    #  continue
    symbols = {'BTC/USD','ETH/BTC'}
    ohlcv = OHLCV(ex,market_data) 
    for symbol in symbols:
      times = 3
      while times > 0 :
        try:
          ohlcv.fetch_and_save_ohlcv(symbol,'1m')
        except Exception as e:
          times = times - 1
        else:
          break

    '''
    with Pool(5) as p:
      p.map(ohlcv.fetch_and_save_ohlcv, symbols)
    '''
  
#download ticker data from input exchanges
def download_ticker(exchanges):
  for ex in exchanges:
    symbols = load_markets(ex)
    if not symbols:
      print('Error: market data of '+ex.id+' cannot be reloaded')
      continue
    ticker = TICKER(ex,market_data)
    for symbol in symbols:
      times = 3
      while times > 0 :
        try:
          ticker.fetch_and_save_ticker(symbol)
        except Exception as e:
          times = times -1
        else:
          break
  

#Test all exchanges and find out those with ohlcv
def test_ohlcv_exchanges(exchanges):
  ochlv_exs=[]
  for ex in exchanges:
    status = None
    times = 3
    while times > 0 :
      try:
        ex.load_markets()
        if ex.has['fetchOHLCV']:
          status = 'true'
          ochlv_exs.append(ex.id)
        else:
          status = 'false'
      except Exception as e:
        times = times - 1
      else:
        break
  print(ochlv_exs)

#Test all exchanges and find out those market data can be accessed without secret&keys
def test_market_public_exs(exs):
  IDs=[]
  for ex in exs:
    times = 3
    while times > 0 :
      try:
        ex.load_markets(True)
      except Exception as e:
        times = times - 1
      else:
        break
    if ex.markets!=None:
      IDs.append(ex.id)
  print(IDs)

def main_function():
  ohlcv_exs = init_ohlcv_exchanges()
  all_public_exs = init_market_public_exchanges()
  sched = BackgroundScheduler()
  sched.add_job(lambda: download_ohlcv(ohlcv_exs), 'interval', minutes=1, id='download_ohlcv')
  sched.add_job(lambda: download_ticker(all_public_exs), 'interval', minutes=1, id='download_ticker')

  print('schedual start')
  sched.start()

  try:
      # This is here to simulate application activity (which keeps the main thread alive).
      while True:
          time.sleep(2)
  except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()

if __name__ == '__main__' :
  #main_function()
  bitstamp = ccxt.bitstamp()
  huobipro = ccxt.huobipro()
  exs = [bitstamp,huobipro]

  pdb.set_trace()
  download_ohlcv(exs)
  download_ticker(exs)



