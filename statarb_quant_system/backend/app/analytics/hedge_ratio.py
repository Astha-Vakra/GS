# backend/app/analytics/hedge_ratio.py

import statsmodels.api as sm
import numpy as np

def calculate_hedge_ratio(x, y):

    x = np.array(x)
    y = np.array(y)

    model = sm.OLS(
        y,
        x
    ).fit()

    beta = model.params[0]

    return beta