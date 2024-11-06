import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def Sharpe(pnl:pd.Series)->float:
    sharpe = pnl.mean() / pnl.std()
    return sharpe

def calculate_Cr(df:pd.DataFrame, window:int)->pd.Series:
    df['return'] = df['close'].astype(float).diff(1).shift(-1) / df['close'].astype(float)
    reversed_data = df['return'][::-1]
    Cr = (reversed_data).rolling(window).sum()[::-1]
    return Cr

def generate_signal(df:pd.DataFrame)->pd.Series:
    N = 20
    k = 2
    Ma = df['close'].rolling(N).mean()
    Sd = df['close'].rolling(N).std()
    Mb = Ma + k*Sd
    Dn = Ma - k*Sd
    raw_Signal = (df['close'] < Dn + 0.5*Sd) * (df['close'] > Dn - 0.5*Sd) * 0.1
    
    # raw_Signal = -(df['close'].astype(float)/df['open'].astype(float) -1)*100
    # raw_Signal = raw_Signal *(raw_Signal>0)
    return raw_Signal

def position_restrict(Signal:pd.Series, window):
    Close_position = Signal.shift(window).fillna(0)
    Position = (Signal - Close_position).cumsum()
    Restrict = abs(Position) <= 1
    new_Signal = (Signal * Restrict).astype(float)
    return new_Signal
    

def calculate_pnl(Position:pd.Series, Cumulative_Return:pd.Series):
    Cumulative_Return = Cumulative_Return.dropna()
    Position = Position.reindex_like(Cumulative_Return)
    pnl = Position * Cumulative_Return
    return pnl
    
def calculate_cost(Position:pd.Series):
    cost = abs(Position.diff()) * 0.00075
    return cost

def main():
    df = pd.read_parquet('2024.parquet')[:]
    window = 10
    Cr = calculate_Cr(df, 5)
    row_Signal = generate_signal(df)
    Signal = position_restrict(row_Signal, window)
    pnl = calculate_pnl(Signal, Cr)
    pnl.index = pd.to_datetime(pnl.index, unit='ms')
    Position = (Signal - Signal.shift(window).fillna(0)).cumsum()
    Position.index = pd.to_datetime(Position.index, unit='ms')
    Position = Position.reindex_like(pnl)
    cost = calculate_cost(Position)
    pnl_net = pnl - cost
    
    plt.figure(figsize=[32, 16])
    p1 = plt.subplot(211)
    p2 = plt.subplot(212)
    p1.plot(pnl.fillna(0).cumsum(), label=f"PNL, Sharpe: {Sharpe(pnl)}")
    p1.plot(pnl_net.fillna(0).cumsum(), label=f"PNL_Net, Sharpe: {Sharpe(pnl_net)}")
    p1.grid(linestyle='--')
    p1.legend(loc='upper left')
    p2.plot(Position, label=f"PNL_Net")
    p2.grid(linestyle='--')
    p2.legend(loc='upper left')
    plt.show()
    
if __name__ == '__main__':
    main()
