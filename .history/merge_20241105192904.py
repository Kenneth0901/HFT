import pandas as pd
import os
from tqdm import tqdm

folder_path = 'data'
parquet_files = [f for f in os.listdir(folder_path) if f.endswith('.parquet')]

df_list = []

for file in tqdm(parquet_files):
    file_path = os.path.join(folder_path, file)
    df = pd.read_parquet(file_path)
    df_list.append(df)

# 将所有DataFrame合并为一个
combined_df = pd.concat(df_list)

# 确保索引按时间戳排序
combined_df.sort_index(inplace=True)

print(combined_df)
