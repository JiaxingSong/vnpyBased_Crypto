import ccxt
from time import time
import pdb

huobipro = ccxt.huobipro()
symbol = 'XRP/USDT'
ts = (time()-5)*1000

pdb.set_trace()
ohlcv = huobipro.fetch_ohlcv(symbol,'1m')