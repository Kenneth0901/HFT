import datetime
import os, os.path
import pandas as pd
import numpy as np
from abc import ABCMeta, abstractmethod

from event import MarketEvent


class DataHandler(object):
    """
    DataHandler is an abstract base class providing an interface for
    all subsequent (inherited) data handlers (both live and historic).

    The goal of a (derived) DataHandler object is to output a generated
    set of bars (OLHCVI) for each symbol requested. 

    This will replicate how a live strategy would function as current
    market data would be sent "down the pipe". Thus a historic and live
    system will be treated identically by the rest of the backtesting suite.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list,
        or fewer if less bars are available.
        """
        raise NotImplementedError("Should implement get_latest_bars()")

    @abstractmethod
    def update_bars(self):
        """
        Pushes the latest bar to the latest symbol structure
        for all symbols in the symbol list.
        """
        raise NotImplementedError("Should implement update_bars()")
    

class HistoricDataHandler(DataHandler):
    """
    HistoricDataHandler is designed to read Parquet files for
    each requested symbol from disk and provide an interface
    to obtain the "latest" bar in a manner identical to a live
    trading interface. 

    crypto无需adj_close来计算return
    """

    def __init__(self, events, dir, symbol_list):
        self.events = events
        self.dir = dir
        self.symbol_list = symbol_list

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True       

        self._open_convert_files()


    def _open_convert_files(self):
        comb_index = None
        for s in self.symbol_list:
            # Load the file with no header information, indexed on date
            self.symbol_data[s] = pd.DataFrame(np.fromfile(os.path.join(self.dir, s+'.dat')))
            self.symbol_data[s].rename(
                columns={
                    '0': 'start_time', 
                    '1': 'open', 
                    '2': 'high', 
                    '3': 'low', 
                    '4': 'close', 
                    '5': 'volume', 
                    '6': 'end_time', 
                    '7': 'quote_volume', 
                    '8': 'trades', 
                    '9': 'taker_base_volume', 
                    '10': 'taker_quote_volume', 
                    '11': 'ignore'
                }, 
                inplace=True
            )
            print(self.symbol_data[s])

            # self.symbol_data[s]['start_time'] = pd.to_datetime(self.symbol_data[s]['start_time'], unit='ms')
            self.symbol_data[s]['end_time'] = pd.to_datetime(self.symbol_data[s]['end_time'], unit='ms')
            self.symbol_data[s].index = pd.to_datetime(self.symbol_data[s].index, unit='ms')
            
            
            # self.symbol_data[s].set_index('start_time', inplace=True)
            self.symbol_data[s].sort_index(inplace=True)

            # Combine the index to pad forward values
            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index.union(self.symbol_data[s].index)

            # Set the latest symbol_data to None
            self.latest_symbol_data[s] = []

        # for s in self.symbol_list:
        #     self.symbol_data[s] = self.symbol_data[s].reindex(
        #         index=comb_index, method='pad'
        #     )
        #     self.symbol_data[s]["returns"] = self.symbol_data[s]["close"].pct_change().dropna()
        #     self.symbol_data[s] = self.symbol_data[s].iterrows()

        # Reindex the dataframes
        for s in self.symbol_list:
            self.symbol_data[s] = self.symbol_data[s].reindex(index=comb_index, method='pad').iterrows()


    def _get_new_bar(self, symbol):
        """
        Returns the latest bar from the data feed as a tuple of 
        (symbol, datetime, open, high, low, close, volume, end_time, qutoe_volume, trades, taker_base_volume, taker_quote_volume).
        """
        for b in self.symbol_data[symbol]:
            yield tuple([symbol, pd.to_datetime(b[0], unit='ms'), 
                        b[1].iloc[0], b[1].iloc[1], b[1].iloc[2], b[1].iloc[3], b[1].iloc[4], b[1].iloc[6], b[1].iloc[7], b[1].iloc[8], b[1].iloc[9]])
            



    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list,
        or N-k if less available.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
        else:
            return bars_list[-N:]
        


    def update_bars(self):
        """
        Pushes the latest bar to the latest_symbol_data structure
        for all symbols in the symbol list.
        """
        for s in self.symbol_list:
            try:
                bar = next(self._get_new_bar(s))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)
        self.events.put(MarketEvent())