# backend/app/analytics/spread.py

import numpy as np

def calculate_spread(
    x,
    y,
    beta
):

    x = np.array(x)
    y = np.array(y)

    spread = y - beta * x

    return spread