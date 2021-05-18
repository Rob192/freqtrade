from datetime import datetime
from math import exp
from typing import Dict

from pandas import DataFrame

from freqtrade.optimize.hyperopt import IHyperOptLoss


class PainToGainHyperOptLoss(IHyperOptLoss):
    """
    Defines the default loss function for hyperopt
    This is intended to give you some inspiration for your own loss function.
    The Function needs to return a number (float) - which becomes smaller for better backtest
    results.
    """

    @staticmethod
    def hyperopt_loss_function(results: DataFrame, trade_count: int,
                               min_date: datetime, max_date: datetime,
                               config: Dict, processed: Dict[str, DataFrame],
                               *args, **kwargs) -> float:
        """
        Objective function, returns smaller number for better results
        """
        total_profit = results['profit_abs'].sum()
        max_loss = results['profit_abs'].min()

        profit_per_trade = results['profit_ratio'].mean()
        trade_duration = results['trade_duration'].mean()

        pain_to_gain = max_loss / total_profit
        duration_per_profit = trade_duration / profit_per_trade

        result = duration_per_profit + pain_to_gain
        return result