import pandas as pd
import os
from tqdm import tqdm

symbol_ls = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'DOGEUSDT', 'ADAUSDT', 'TRXUSDT', ]


for symbol in tqdm(symbol_ls):
    folder_path = f'./data/{symbol}'
    files = [f for f in os.listdir(folder_path) if f.endswith('.pkl')]
    df_list = []
    sav_path = f'./merge/'
    os.makedirs(sav_path, exist_ok=True)
    for file in files:
        file_path = os.path.join(folder_path, file)
        df = pd.read_pickle(file_path)
        df_list.append(df)

    combined_df = pd.concat(df_list)
    combined_df.sort_index(inplace=True)
    combined_df = combined_df.astype(float)
    combined_df[['end_time', 'ignore']] = combined_df[['end_time', 'ignore']].astype('Int64')
    combined_df.to_pickle(f'./merge/{symbol}.pkl')
