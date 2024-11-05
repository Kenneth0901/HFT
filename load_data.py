import pandas as pd
import requests
import time
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='load_data.log', mode='w')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


BASE_URL = 'https://api.binance.com'
kline = '/api/v3/klines'
limit = 1000
symbol = 'BTCUSDT'
end_time = int(time.time() //60 *60 * 1000) #转化为毫秒 ms时间戳
start_time = int(end_time - limit * 60 * 1000)


folder_path = f'./data/{symbol}'
os.makedirs(folder_path, exist_ok=True)

while end_time > 1704067200000:
    url = BASE_URL + kline + '?symbol=' + str(symbol) + '&interval=1m&limit=' + str(limit) + '&startTime=' + str(start_time) + '&endTime=' + str(end_time)
    res = requests.get(url)
    status_code = res.status_code
    if status_code == 200:
        data = res.json()
        df = pd.DataFrame(res.json(), columns = {'start_time': '0', 'open': '1', 'high': '2', 'low': '3', 'close': '4', 'volume': '5', 'end_time': '6', 
                                         'quote_volume': '7', 'trades': '8', 'taker_base_volume': '9', 'taker_quote_volume': '10', 'ignore': '11'})
        df.set_index('start_time', inplace=True)
        df.to_parquet(f'./data/{symbol}/{end_time}')
        logger.info(f'finish {end_time}')
        end_time = start_time
        start_time = int(end_time - limit * 60 * 1000)
        
    else:
        logger.error(f'Error in {end_time}')
        time.sleep(5)
        continue
        
