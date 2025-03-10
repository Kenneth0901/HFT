import numpy as np
import pandas as pd


start_date = "2024-01-01"
end_date = "2025-03-08"
date_ls = pd.date_range(start=start_date, end=end_date, freq="D")\


for date in date_ls[:]:
            # time.sleep(1)
            timestamp = int(date.timestamp() * 1000)
            date_str = date.strftime("%Y%m%d")
            save_path = os.path.join(r'C:\Users\yy\Desktop\HFT_zxy\data', date_str, symbol, '1sbar.dat')