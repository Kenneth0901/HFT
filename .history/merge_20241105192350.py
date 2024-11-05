import pandas as pd
import os

# 指定文件夹路径
folder_path = 'data'

# 获取文件夹中所有parquet文件的路径
parquet_files = [f for f in os.listdir(folder_path) if f.endswith('.parquet')]

# 初始化一个空的DataFrame列表
df_list = []

for file in tqdm(parquet_files):
    file_path = os.path.join(folder_path, file)
    df = pd.read_parquet(file_path)
    
    
    df_list.append(df)

# 将所有DataFrame合并为一个
combined_df = pd.concat(df_list)

# 确保索引按时间戳排序
combined_df.sort_index(inplace=True)

# 输出合并后的DataFrame
print(combined_df)
