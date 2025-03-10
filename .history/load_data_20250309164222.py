import pandas as pd
import requests
import time
from loguru import logger
import os
from multiprocessing.pool import ThreadPool  # 使用 ThreadPool 替代 Pool
from multiprocessing import freeze_support
from datetime import datetime
import numpy as np

# 配置日志
logger.add("download.log", rotation="10 MB", level="INFO")

# 币安API配置
BASE_URL = 'https://api.binance.com'
kline = '/api/v3/klines'
limit = 800
symbol = 'BTCUSDT'
weight_limit = 6000  # 币安API每分钟权重限制
weight_buffer = 64  # 权重缓冲，避免刚好达到限制

# 日期范围
start_date = "2024-01-01"
end_date = "2025-03-09"
date_ls = pd.date_range(start=start_date, end=end_date, freq="D")

def fetch_data(symbol, limit, start_time):
    """获取K线数据"""
    url = f"{BASE_URL}{kline}?symbol={symbol}&interval=1s&limit={limit}&startTime={start_time}&endTime={start_time + (limit * 1000)}"
    try:
        res = requests.get(url)
        res.raise_for_status()  # 检查请求是否成功
        data = res.json()
        # 获取当前权重使用情况
        used_weight = int(res.headers.get('X-MBX-USED-WEIGHT-1M', 0))
        logger.info(f"Fetched data for {start_time}, used weight: {used_weight}")
        return data, used_weight
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data: {e}")
        return None, 0

def check_weight(used_weight):
    """检查权重是否接近限制，如果是则暂停"""
    if used_weight >= (weight_limit - weight_buffer):
        logger.warning(f"Weight接近限制: {used_weight}, 暂停60秒")
        time.sleep(10)  # 暂停10秒以重置权重计数器

def main():
    """主函数"""
    for date in date_ls:
        timestamp = int(date.timestamp() * 1000)
        date_str = date.strftime("%Y%m%d")
        save_path = os.path.join(r'C:\Users\yy\Desktop\HFT_zxy\data', date_str, symbol, '1sbar.dat')
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # 使用 ThreadPool 替代 Pool
        with ThreadPool() as pool:  # 控制线程数量
            results = pool.starmap(fetch_data, [(symbol, limit, timestamp + i * limit * 1000) for i in range(108)])

        # 处理结果
        data_ls = []
        for data, used_weight in results:
            if data:
                data_ls.append(data)
            check_weight(used_weight)  # 检查权重并限速

        if data_ls:
            df = np.concatenate(data_ls, axis=0).astype(np.float32)
            df.tofile(save_path)
            logger.info(f'Finished downloading data in {date_str}')
        else:
            logger.warning(f'No data fetched for {date_str}')

if __name__ == '__main__':
    freeze_support()  # 在 Windows 上必须调用
    main()





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
