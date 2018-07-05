import h5py
import numpy as np
import pandas as pd
import pdb

MAX_BUFFER_SIZE = 1024

class ccxtMarketData(object):
  def __init__(self):
     #constructor
     self.exchanges = {} 
     self.channel = {}


  def __save__(self, ch):

     print('__save__'+ch)
     strs = ch.split('_');
     filename = strs[0]+'_ohlcv.h5'

     values = np.array(self.channel[ch].values, dtype=np.float64)
     id_loc = np.where(self.channel[ch].columns == 'id')[0][0]
     values = values[values[:, id_loc].argsort()]

     f = h5py.File(filename)
     if ch not in f.keys():
         f.create_dataset(ch, values.shape, maxshape=(None, values.shape[1]), dtype=np.float64)
         f[ch][:, :] = values
         f.close()
         return

     dset = f[ch]
     last_id = dset[-1, id_loc]
     values = np.delete(values, np.where(values[:, id_loc] <= last_id), axis=0)
     if values.size > 0:
         dset.resize((dset.shape[0] + values.shape[0], values.shape[1]))
         dset[-values.shape[0]:, :] = values
     f.close()
  
  def update_to_buffer(self, ch, data):
     if ch not in self.channel.keys():
       self.channel[ch] = pd.DataFrame()
     self.channel[ch] = pd.concat([data, self.channel[ch]])
     self.channel[ch].drop_duplicates(inplace=True)
     #if self.channel[ch].size > MAX_BUFFER_SIZE:
     self.__save__(ch)

  def parse_history_trade(self, exchange, symbol, trades):
     ch = exchange.id+'_'+symbol.replace('/','_')+'trades'
     data = []
     for each_trade in trades:
         data.extend(each_trade)
     data = pd.DataFrame(data)
     data.ix[data['side'] == 'buy', 'side'] = 1
     data.ix[data['side'] == 'sell', 'side'] = -1

     return ch, data

  def save_data(self,exchange,symbol,ticker,order_book,trades,OHLCV):
    ch,ticker_data = self.parse_ticker(exchange,symbol,ticker)
    self.update_to_buffer(ch, ticker_data)

class OHLCV:
  def __init__(self,ex,marketData):
     #constructor
     self.exchange = ex 
     self.marketData = marketData
     self.max_len = 0

  def parse_ohlcv(self, symbol, OHLCV, timeframe):
     ch = self.exchange.id+'_'+symbol.replace('/','_')+'_'+timeframe+'_ohlcv'
     data = pd.DataFrame(OHLCV)
     if len(data.columns) != 6:
       data = pd.DataFrame([])
       return ch,data
     data.columns = ['id','open','high','low','close','volumn']

     return ch, data

  def save_ohlcv(self, symbol, OHLCV, timeframe):
    ch,ohlcv_data = self.parse_ohlcv(symbol,OHLCV,timeframe)
    if not ohlcv_data.empty:
      self.marketData.update_to_buffer(ch,ohlcv_data)
    else:
      print('Data Empty: '+ ch)


  def fetch_and_save_ohlcv(self, symbol,timeframe):
      OHLCV = None
      times = 3
      #since = None
      while times > 0 :
        try:
          OHLCV = self.exchange.fetch_ohlcv(symbol,timeframe)
        except Exception as e:
          times = times - 1
        else:
          break
      if len(OHLCV) > self.max_len:
        self.max_len = len(OHLCV) 
      self.save_ohlcv(symbol,OHLCV,timeframe)
      

class TICKER:
  def __init__(self,ex,md):
    #constructor
    self.exchange = ex
    self.marketData = md

  def parse_ticker(self,symbol,ticker):
    ch = self.exchange.id+'_'+symbol.replace('/','_')+'_ticker'
    print(ch)
    if ticker==None:
     return ch, pd.DataFrame([]) 

    if 'info' in ticker:
      info = ticker['info']
      del ticker['info']
      for key in ticker.keys():
        if key in info and info[key]!=ticker[key] and type(info[key])==type(ticker[key]):
          ticker[key]=info[key] 
    del ticker['datetime']
    del ticker['symbol'] 
    if 'bidVolume' in ticker:
      del ticker['bidVolume']
    if 'askVolume' in ticker:
      del ticker['askVolume']
    tick = list(ticker.values())
    data = pd.DataFrame(tick).T
    data.columns = ['id','high','low','bid','ask','vwap','open'
                    ,'close','first','last','change','percentage'
                    ,'average','baseVol','quoteVol']
    return ch,data

  def save_ticker(self,symbol,ticker):
    ch,ticker_data = self.parse_ticker(symbol,ticker)
    if not ticker_data.empty:
      self.marketData.update_to_buffer(ch,ticker_data)
    else:
      print('Data Empty: '+ ch)

  def fetch_and_save_ticker(self,symbol):
    ticker = None
    times = 3
    while times > 0:
      try:
        ticker = self.exchange.fetch_ticker(symbol) 
      except Exception as e :
        times = times -1
      else:
        break
    self.save_ticker(symbol,ticker)
 
