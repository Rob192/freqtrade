# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401

# --- Do not remove these libs ---
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from functools import reduce

from freqtrade.strategy import IStrategy
from freqtrade.strategy import CategoricalParameter, DecimalParameter, IntParameter
from freqtrade.exchange import timeframe_to_minutes

# --------------------------------
# Add your lib to import here
import talib.abstract as sta
import pandas_ta as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class TrendHyperOpt(IStrategy):
    """
    This is a strategy template to get you started.
    More information in https://www.freqtrade.io/en/latest/strategy-customization/

    You can:
        :return: a Dataframe with all mandatory indicators for the strategies
    - Rename the class name (Do not forget to update class_name)
    - Add any methods you want to build your strategy
    - Add any lib you need to build your strategy

    You must keep:
    - the lib in the section "Do not remove these libs"
    - the methods: populate_indicators, populate_buy_trend, populate_sell_trend
    You should keep:
    - timeframe, minimal_roi, stoploss, trailing_*
    """
    lookback = IntParameter(10, 80, default=20, space='buy')

    buy_rsi = IntParameter(53, 54, default=53, space="buy")
    buy_roc = IntParameter(102, 103, default=102, space="buy")

    buy_ema_short = IntParameter(3, 50, default=5, space='buy')
    buy_ema_long = IntParameter(10, 100, default=50, space='buy')
    buy_trigger = CategoricalParameter(['rsi', 'ema', 'roc'], space="buy")


    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 2

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    max_hold = "1d"
    timeframe_mins = timeframe_to_minutes(max_hold)
    minimal_roi = {
        str(timeframe_mins): -100000.0, #after one day, sell everything, at any price
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.10

    # Trailing stoploss
    trailing_stop = False
    # trailing_only_offset_is_reached = False
    # trailing_stop_positive = 0.01
    # trailing_stop_positive_offset = 0.0  # Disabled / not configured

    # Optimal timeframe for the strategy.
    timeframe = '5m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the "ask_strategy" section in the config.
    use_sell_signal = True
    sell_profit_only = False
    ignore_roi_if_buy_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = max(lookback.value, buy_ema_long.value)

    # Optional order type mapping.
    order_types = {
        'buy': 'limit',
        'sell': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'buy': 'gtc',
        'sell': 'gtc'
    }
    
    plot_config = {
        # Main plot indicators (Moving averages, ...)
        'main_plot': {
            'tema': {},
            'sar': {'color': 'white'},
        },
        'subplots': {
            # Subplots - each dict defines one additional plot
            "MACD": {
                'macd': {'color': 'blue'},
                'macdsignal': {'color': 'orange'},
            },
            "RSI": {
                'rsi': {'color': 'red'},
            }
        }
    }
    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame

        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        :param dataframe: Dataframe with data from the exchange
        :param metadata: Additional information, like the currently traded pair
        :return: a Dataframe with all mandatory indicators for the strategies
        """
        

        # RSI
        for val in self.lookback.range:
            dataframe[f'rsi_{val}'] = dataframe.ta.rsi(length=val)

        # Calculate all ema_short values
        for val in self.buy_ema_short.range:
            dataframe[f'ema_short_{val}'] = sta.EMA(dataframe, timeperiod=val)

        # Calculate all ema_long values
        for val in self.buy_ema_long.range:
            dataframe[f'ema_long_{val}'] = sta.EMA(dataframe, timeperiod=val)

        # ROC
        for val in self.lookback.range:
            dataframe[f'roc_{val}'] = sta.ROC(dataframe, window=val)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        conditions = []
        # GUARDS AND TRENDS

        # TRIGGERS
        if self.buy_trigger.value == 'rsi':
            conditions.append(dataframe[f'rsi_{self.lookback.value}'] > self.buy_rsi.value)
        if self.buy_trigger.value == 'ema':
            conditions.append(qtpylib.crossed_above(
                dataframe[f'ema_short_{self.buy_ema_short.value}'], dataframe[f'ema_long_{self.buy_ema_long.value}']
            ))
        if self.buy_trigger.value == 'roc':
            conditions.append(dataframe[f'roc_{self.lookback.value}'] > self.buy_rsi.value)

        # Check that volume is not 0
        conditions.append(dataframe['volume'] > 0)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        dataframe['sell'] = 0 # Sell only on Roi indication
        return dataframe
    