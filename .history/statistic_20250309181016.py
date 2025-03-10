import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm

# 生成数据
start_date = "2024-01-01"
end_date = "2025-03-08"
date_ls = pd.date_range(start=start_date, end=end_date, freq="D")
symbol = "BTCUSDT"
data_ls = []

for date in date_ls[:]:
    timestamp = int(date.timestamp() * 1000)
    date_str = date.strftime("%Y%m%d")
    save_path = os.path.join(r'C:\Users\yy\Desktop\HFT_zxy\data', date_str, symbol, '1sbar.dat')
    data = np.fromfile(save_path, dtype=np.float32).reshape(-1, 12)[:, 4]  # 提取第 4 列（假设是价格）
    data_ls.append(data)

# 合并数据并计算收益率
df = np.concatenate(data_ls)
r = np.diff(df) / df[:-1]

# 标准化 r
r_standardized = (r - np.mean(r)) / np.std(r)

# 绘制 KDE 图像
plt.figure(figsize=(10, 6))
sns.kdeplot(r_standardized, label="Standardized Returns (KDE)", color="blue", linestyle="-")

# 绘制标准正态分布
x = np.linspace(-5, 5, 1000)  # 定义 x 轴范围
plt.plot(x, norm.pdf(x, 0, 1), label="Standard Normal Distribution", color="red", linestyle="--")

# 添加图例和标签
plt.legend()
plt.title("KDE of Standardized Returns vs Standard Normal Distribution")
plt.xlabel("Value")
plt.ylabel("Density")

# 显示图像
plt.show()