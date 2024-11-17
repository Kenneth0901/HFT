from datahandler import HistoricDataHandler
from execution import SimulatedExecutionHandler
from portfolio import NaivePortfolio
from strategy import BollStrategy
import queue
from time import time
import pandas as pd


start_date = pd.to_datetime(1704154200000, unit='ms')

events = queue.Queue(maxsize=0)
bars = HistoricDataHandler(events, './merge', ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'DOGEUSDT', 'ADAUSDT', 'TRXUSDT'])
port = NaivePortfolio(bars, events, start_date)
strategy = BollStrategy(bars, port, events)
broker = SimulatedExecutionHandler(bars, events)


while True:
    # Update the bars (specific backtest code, as opposed to live trading)
    if bars.continue_backtest == True:
        bars.update_bars()
    else:
        break
    # Handle the events
    while True:
        try:
            event = events.get(False)
        except queue.Empty:
            break
        else:
            if event is not None:
                if event.type == 'MARKET':
                    strategy.calculate_signals(event)
                    port.update_positions_and_holdings(event)

                elif event.type == 'SIGNAL':
                    port.update_signal(event)

                elif event.type == 'ORDER':
                    broker.execute_order(event)

                elif event.type == 'FILL':
                    port.update_fill(event)



port.create_equity_curve_dataframe()
port.output_summary_stats()
port.plot_pnl()

    # 10-Minute heartbeat
    # time.sleep(60)