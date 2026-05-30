# backend/app/analytics/zscore.py

import numpy as np

def calculate_zscore(spread):

    mean = np.mean(spread)

    std = np.std(spread)

    if std == 0:
        return 0

    zscore = (
        spread[-1] - mean
    ) / std

    return zscore