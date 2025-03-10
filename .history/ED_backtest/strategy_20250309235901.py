import datetime
import numpy as np
import pandas as pd
from queue import Queue

from abc import ABCMeta, abstractmethod
from portfolio import NaivePortfolio
from event import SignalEvent, OrderEvent



class Strategy(object):
    """
    Strategy is an abstract base class providing an interface for
    all subsequent (inherited) strategy handling objects.

    The goal of a (derived) Strategy object is to generate Signal
    objects for particular symbols based on the inputs of Bars 
    (OLHCVI) generated by a DataHandler object.

    This is designed to work both with historic and live data as
    the Strategy object is agnostic to the data source,
    since it obtains the bar tuples from a queue object.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def calculate_signals(self):
        """
        Provides the mechanisms to calculate the list of signals.
        """
        raise NotImplementedError("Should implement calculate_signals()")
    


class BuyAndHoldStrategy(Strategy):
    """
    This is an extremely simple strategy that goes LONG all of the 
    symbols as soon as a bar is received. It will never exit a position.

    It is primarily used as a testing mechanism for the Strategy class
    as well as a benchmark upon which to compare other strategies.
    """

    def __init__(self, bars, events):
        """
        Initialises the buy and hold strategy.

        Parameters:
        bars - The DataHandler object that provides bar information
        events - The Event Queue object.
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events

        # Once buy & hold signal is given, these are set to True
        self.bought = self._calculate_initial_bought()


    def _calculate_initial_bought(self):
        """
        Adds keys to the bought dictionary for all symbols
        and sets them to False.
        """
        bought = {}
        for s in self.symbol_list:
            bought[s] = False
        return bought
    

    def calculate_signals(self, event):
        """
        For "Buy and Hold" we generate a single signal per symbol
        and then no additional signals. This means we are 
        constantly long the market from the date of strategy
        initialisation.

        Parameters
        event - A MarketEvent object. 
        """
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars(s, N=1)
                if bars is not None and bars != []:
                    if self.bought[s] == False:
                        # (Symbol, Datetime, Type = LONG, SHORT or EXIT)
                        signal = SignalEvent(bars[0][0], bars[0][1], 'LONG')
                        self.events.put(signal)
                        self.bought[s] = True  


class MixTechStrategy(Strategy):

    def __init__(self, bars, port:NaivePortfolio, events) -> None:
        """
        MACD+RSI+EMA判断开仓平仓
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.port = port
        self.initial_capital = port.initial_capital
        self.ema_s = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        self.ema_l = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        self.macd = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        self.signal = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )

    def cal_boll(self, close:pd.Series):
        ma = close.mean()
        std = close.std()
        floor = ma - 2*std
        top = ma + 2*std
        return ma, std, floor, top
    
    def cal_rsi(self, close:pd.Series):
        rtn = close.pct_change()
        gain = rtn[rtn>0].sum()
        loss = -rtn[rtn<0].sum()
        rs = gain/(loss+0.00000000000001)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def update_index(self, bars):
        if self.ema_s[bars[-1][0]] == 0.0:
            self.ema_s[bars[-1][0]] = bars[-1][5]

        if self.ema_l[bars[-1][0]] == 0.0:
            self.ema_l[bars[-1][0]] = bars[-1][5]

        self.ema_s[bars[-1][0]] = 0.08*bars[-1][5] + 0.92*self.ema_s[bars[-1][0]]
        self.ema_l[bars[-1][0]] = 0.04*bars[-1][5] + 0.96*self.ema_l[bars[-1][0]]
        self.macd[bars[-1][0]] = self.ema_s[bars[-1][0]] - self.ema_l[bars[-1][0]]
        self.signal[bars[-1][0]] = 0.04*self.macd[bars[-1][0]] +0.96*self.signal[bars[-1][0]]
        
    #bar格式如下
    # (0: symbol, 1: datetime, 2: open, 3: high, 4: low, 5: close, 6: volume, 7: qutoe_volume, 8: trades, 9: taker_base_volume, 10: taker_quote_volume).

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            new_order_history = []
            N = 20


            for s in self.symbol_list:

                ####################################
                bars = self.bars.get_latest_bars(s, N)
                self.update_index(bars)
                if len(bars) >= N:
                    close = pd.DataFrame(bars)[5]
                    boll_5 = self.cal_boll(close[-20:])
                    rsi = self.cal_rsi(close[-20:])
                    if  bars[-1][5] >=self.ema_l[s] and self.macd[s] >= self.signal[s] and rsi>=50:
                        # (Symbol, Datetime, Type = LONG, SHORT)
                        signal = SignalEvent(bars[-1][0], bars[-1][1], 'LONG', strength= self.initial_capital/bars[-1][5]*0.1)
                        self.events.put(signal)
                    
                    for order in [o for o in self.port.order_history if o['symbol'] == s]:
                        if  (bars[-1][5] < self.ema_l[s] and self.macd[s] < self.signal[s] and rsi<50) \
                            or order['price'] <= bars[-1][5]*0.95 \
                            or order['price'] >= bars[-1][5]*1.1:
                            order_event = OrderEvent(order['symbol'], 'MKT', order['quantity'], 'SELL', order_mark='CLOSE')
                            self.events.put(order_event)
                        else: new_order_history.append(order)
                #####################################

            self.port.order_history = new_order_history



                        
##############################################################
class BollandMACDStrategy(Strategy):

    def __init__(self, bars, port:NaivePortfolio, events) -> None:
        """
        布林带下轨建仓，10%止盈止损
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.port = port
        self.initial_capital = port.initial_capital
        self.ema_s = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        self.ema_l = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        self.macd = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        self.signal = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )

    def cal_boll(self, close:pd.Series):
        ma = close.mean()
        std = close.std()
        floor = ma - 3*std
        top = ma + 3*std
        return ma, std, floor, top
    

    def update_index(self, bars):
        if self.ema_s[bars[-1][0]] == 0.0:
            self.ema_s[bars[-1][0]] = bars[-1][5]

        if self.ema_l[bars[-1][0]] == 0.0:
            self.ema_l[bars[-1][0]] = bars[-1][5]

        self.ema_s[bars[-1][0]] = 0.08*bars[-1][5] + 0.92*self.ema_s[bars[-1][0]]
        self.ema_l[bars[-1][0]] = 0.04*bars[-1][5] + 0.96*self.ema_l[bars[-1][0]]
        self.macd[bars[-1][0]] = self.ema_s[bars[-1][0]] - self.ema_l[bars[-1][0]]
        self.signal[bars[-1][0]] = 0.04*self.macd[bars[-1][0]] +0.96*self.signal[bars[-1][0]]
        
    #bar格式如下
    # (0: symbol, 1: datetime, 2: open, 3: high, 4: low, 5: close, 6: volume, 7: qutoe_volume, 8: trades, 9: taker_base_volume, 10: taker_quote_volume).

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            new_order_history = []
            N = 100
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars(s, 100)
                self.update_index(bars)
                if len(bars) >= N:
                    close = pd.DataFrame(bars)[::5][5]
                    boll_5 = self.cal_boll(close[-20:])
                    if  bars[-1][5] <= boll_5[2] and self.macd[bars[-1][0]] >= self.signal[bars[-1][0]]*1.03:
                        # (Symbol, Datetime, Type = LONG, SHORT)
                        signal = SignalEvent(bars[-1][0], bars[-1][1], 'LONG', strength= self.initial_capital/bars[-1][5]*0.01)
                        self.events.put(signal)
                    

                    for order in [o for o in self.port.order_history if o['symbol'] == s]:
                        if  bars[-1][5] <= order['price']*0.95 or bars[-1][5] >= order['price']*1.01:
                            order_event = OrderEvent(order['symbol'], 'MKT', order['quantity'], 'SELL', order_mark='CLOSE')
                            self.events.put(order_event)
                        else: new_order_history.append(order)

            self.port.order_history = new_order_history
       



class StableTrendStrategy(Strategy):
    """
    稳定趋势策略核心逻辑：
    1. 使用通道突破作为入场信号
    2. ATR动态止损止盈
    3. 基于波动率的头寸管理
    4. 双重趋势过滤机制
    """
    def __init__(self, bars, port: NaivePortfolio, events):
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.port = port
        self.initial_capital = port.initial_capital
        
        # 策略参数
        self.entry_period = 128      # 通道周期
        self.atr_period = 64        # 波动率周期
        self.risk_ratio = 1      # 单笔风险比例
        self.trend_filter = 1000     # 趋势过滤均线
        self.N = 10
        
        # 状态存储
        self.stop_loss = {s:0 for s in self.symbol_list}
        self.entry_level = {s:0 for s in self.symbol_list}

    def calculate_indicators(self, symbol):
        """计算必要指标"""
        bars = self.bars.get_latest_bars(symbol, self.entry_period)
        if len(bars) < self.entry_period:
            return None

        closes = [b[5] for b in bars]
        highs = [b[3] for b in bars]
        lows = [b[4] for b in bars]
        
        # 计算通道和ATR
        upper = max(highs[-self.entry_period:])
        lower = min(lows[-self.entry_period:])
        atr = self.calculate_atr(highs, lows, closes)
        
        # 计算趋势过滤
        ma_long = sum(closes) / len(closes)
        current_close = closes[-1]
        
        return {
            'upper': upper,
            'lower': lower,
            'atr': atr,
            'ma_filter': ma_long,
            'price': current_close
        }

    def calculate_atr(self, highs, lows, closes):
        """计算真实波动范围"""
        tr = []
        for i in range(1, len(closes)):
            hl = highs[i] - lows[i]
            hc = abs(highs[i] - closes[i-1])
            lc = abs(lows[i] - closes[i-1])
            tr.append(max(hl, hc, lc))
        return sum(tr[-self.atr_period:]) / self.atr_period

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            new_order_history = []
            for s in self.symbol_list:
                # 获取最新K线数据（包含时间戳）
                bars = self.bars.get_latest_bars(s, 1)
                if not bars:
                    continue
                
                # 从K线数据获取正确的时间戳
                timestamp = bars[-1][1]  # 使用K线数据中的时间戳

                data = self.calculate_indicators(s)
                if not data:
                    continue
                
                position = self.port.current_positions[s]
                cash = self.port.current_holdings['cash']
                price = data['price']

                # ...（中间逻辑保持不变）

                # 修正后的信号生成
                if price >= data['upper'] and price >=data['ma_filter']:
                    if self.port.current_positions[s] < 0:
                        self.events.put(SignalEvent(s, timestamp, 'EXIT',0))
                    self.events.put(SignalEvent(s, timestamp, 'LONG', self.initial_capital*self.risk_ratio / self.N*data['atr']/price))  # 使用正确的timestamp
                    pass
                    
                elif price <= data['lower'] and price <= data['ma_filter']:
                    if self.port.current_positions[s] > 0:
                        self.events.put(SignalEvent(s, timestamp, 'EXIT',0))
                    self.events.put(SignalEvent(s, timestamp, 'SHORT', self.initial_capital*self.risk_ratio / self.N*data['atr']/price))  # 使用正确的timestamp
                    pass

                for order in [o for o in self.port.order_history if o['symbol'] == s]:
                        if order['direction'] =='BUY':
                            if  bars[-1][5]>order['price']+self.N*data['atr'] or bars[-1][5]<order['price']-self.N*data['atr'] or order['flag']==100:
                                self.events.put(SignalEvent(s, timestamp, 'EXIT',0))
                                
                            else: 
                                order['flag'] += 1
                                new_order_history.append(order)
                                
                        else:
                            if  bars[-1][5]<order['price']-self.N*data['atr'] or bars[-1][5]>order['price']+self.N*data['atr'] or order['flag']==100:
                                self.events.put(SignalEvent(s, timestamp, 'EXIT',0))
                                
                            else: 
                                order['flag'] += 1
                                new_order_history.append(order)

            self.port.order_history = new_order_history