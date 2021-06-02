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
        initial_stake_amount = results['stake_amount'].iloc[0]
        count_win = results[results['profit_ratio'] > 0]['profit_ratio'].count()
        avg_win = results[results['profit_ratio'] > 0]['profit_ratio'].mean()

        count_loss = results[results['profit_ratio'] < 0]['profit_ratio'].count()
        avg_loss = results[results['profit_ratio'] < 0]['profit_ratio'].mean()

        total_profit = max(0.1,results['profit_abs'].sum()) #avoid negative results
        total_profit_ratio = total_profit / initial_stake_amount #we compare the profit vs initial stake

        total_expected_profit_ratio = pow(1 + avg_win, count_win) * pow(1+avg_loss, count_loss) #we compare the expected profit vs initial stake
        max_loss = abs(results['profit_ratio'].min())

        # profit_per_trade = results['profit_ratio'].mean()
        # trade_duration = results['trade_duration'].mean()

        pain_to_gain = max_loss / pow(total_expected_profit_ratio, 2)
        # duration_per_profit = trade_duration / profit_per_trade

        result = pain_to_gain
        return result