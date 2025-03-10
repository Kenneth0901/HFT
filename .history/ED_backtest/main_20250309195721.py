import queue
import time
from datetime import datetime
import pandas as pd
import logging
import os 

from datahandler import HistoricDataHandler
from execution import SimulatedExecutionHandler
from portfolio import NaivePortfolio
from strategy import MixTechStrategy, BollandMACDStrategy, MartinStrategy

log_path = './ED_backtest/logs/'
os.makedirs(log_path, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=f'''./ED_backtest/logs/test.log''', mode='w')
# handler = logging.FileHandler(filename=f'''./ED_backtest/logs/{datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H-%M-%S')}.log''', mode='w')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

start_date = pd.to_datetime(1704094200000, unit='ms')

events = queue.Queue(maxsize=0)
bars = HistoricDataHandler(events, r'./bar_data', ['BTCUSDT'])
port = NaivePortfolio(bars, events, start_date)
strategy = BollandMACDStrategy(bars, port, events)
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
                    logger.info(f'''Total: {port.all_holdings[-1]['total']}''')

                elif event.type == 'SIGNAL':
                    logger.info(f'Signal at {event.datetime}')
                    port.update_signal(event)

                elif event.type == 'ORDER':
                    broker.execute_order(event)

                elif event.type == 'FILL':
                    logger.info(f'{event.timestamp} {event.symbol} {event.direction} {event.quantity} {event.fill_cost}')
                    port.update_fill(event)


port.create_equity_curve_dataframe()
port.output_summary_stats()
port.plot_pnl()

    # 10-Minute heartbeat
    # time.sleep(60)