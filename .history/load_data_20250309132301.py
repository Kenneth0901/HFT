import pandas as pd
import requests
import time
import logging
import os
from multiprocess import managers
from datetime import datetime
# 设置日志记录
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='load_data.log', mode='w')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

BASE_URL = 'https://api.binance.com'
kline = '/api/v3/klines'
limit = 800


date_str = "20250309 00:00"
end = int(datetime.strptime(date_str, "%Y%m%d %H:%M").timestamp()*1000)
start = end - limit*1000




# symbol_ls = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'DOGEUSDT', 'ADAUSDT', 'TRXUSDT', 'AVAXUSDT', 'SHIBUSDT', 'XLMUSDT',\
#              'WBTCUSDT', 'DOTUSDT', 'LINKUSDT']

# 为每个符号创建数据文件夹
# for symbol in symbol_ls:
#     folder_path = f'./data/{symbol}'
#     os.makedirs(folder_path, exist_ok=True)

#     start = 1704154200000  # 2024-01-01 08:10:00 
#     end = 1731814200000  # 2024-11-17 11:30:00  以end为主,start随意，我是根据跑出来结果改的start
#     end_time = int(end)  # 转化为毫秒 ms 时间戳
#     start_time = int(end_time - limit * 60 * 1000)

#     while end_time >= start:  # 2024-01-01 08:10:00
#         file_path = f'./data/{symbol}/{end_time}.pkl'


#         if os.path.exists(file_path):
#             end_time = start_time
#             start_time = int(end_time - limit * 60 * 1000)
#             continue

#         url = f"{BASE_URL}{kline}?symbol={symbol}&interval=1m&limit={limit}&startTime={start_time}&endTime={end_time}"
#         res = requests.get(url)
#         status_code = res.status_code

#         if status_code == 200:
#             data = res.json()
#             if data:
#                 df = pd.DataFrame(data, columns=[
#                     'start_time', 'open', 'high', 'low', 'close', 'volume', 
#                     'end_time', 'quote_volume', 'trades', 
#                     'taker_base_volume', 'taker_quote_volume', 'ignore'
#                 ])
#                 df.set_index('start_time', inplace=True)
#                 df.to_pickle(file_path)
#                 logger.info(f'Successfully saved data for {symbol} at {end_time}')
#             else:
#                 logger.warning(f'No data returned for {symbol} at {end_time}')
            
#             end_time = start_time
#             start_time = int(end_time - limit * 60 * 1000)

#         else:
#             logger.error(f'Error fetching data for {symbol} at {end_time}, status code: {status_code}')
#             time.sleep(5) 

#     logger.info(f'Finished downloading data for {symbol}')
