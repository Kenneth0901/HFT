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

                        

class BollStrategy(Strategy):
    def __init__(self, bars, port:NaivePortfolio, events) -> None:
        """
        布林带下轨建仓，10%止盈止损
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.port = port


    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars(s, N=100)
                new_order_history = []
                if bars is not None and bars != []:
                        
                    #bar格式如下

                    # (0: symbol, 1: datetime, 2: open, 3: low, 4: high, 5: volume, 6: end_time, 
                    # 7: qutoe_volume, 8: trades, 9: taker_base_volume, 10: taker_quote_volume).
                    close = pd.DataFrame(bars)[5].rolling(5).mean()[::5]
                    ma = close.mean()
                    std = close.std()
                    floor = ma - 3*std
                    top = ma + 3*std
                    if bars[-1][5] <= floor:
                        # (Symbol, Datetime, Type = LONG, SHORT or EXIT)
                        signal = SignalEvent(bars[0][0], bars[0][1], 'LONG', strength=0.1)
                        self.events.put(signal)
                    

                    for order in self.port.order_history:
                        if  bars[-1][5] <= order['price']*0.95 or bars[-1][5] >= order['price']*1.02:
                            order_event = OrderEvent(order['symbol'], 'MKT', order['quantity'], 'SELL')
                            self.events.put(order_event)
                        else: new_order_history.append(order)

                self.port.order_history = new_order_history

                    



        