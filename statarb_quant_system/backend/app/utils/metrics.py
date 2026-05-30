# backend/app/utils/metrics.py

import numpy as np

def calculate_sharpe_ratio(
    equity_curve
):

    returns = np.diff(
        equity_curve
    )

    if len(returns) == 0:
        return 0

    std = np.std(returns)

    if std == 0:
        return 0

    sharpe = (
        np.mean(returns)
        / std
    ) * np.sqrt(252)

    return sharpe


def calculate_max_drawdown(
    equity_curve
):

    peak = equity_curve[0]

    max_dd = 0

    for value in equity_curve:

        if value > peak:
            peak = value

        dd = (
            peak - value
        ) / peak

        max_dd = max(
            max_dd,
            dd
        )

    return max_dd * 100