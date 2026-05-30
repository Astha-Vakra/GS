# backend/app/backtest/statarb_backtest.py

import yfinance as yf
import pandas as pd
import numpy as np

from app.config import (
    PAIRS,
    LOOKBACK_WINDOW,
    ENTRY_ZSCORE,
    EXIT_ZSCORE,
    INITIAL_CAPITAL
)

from app.analytics.hedge_ratio import (
    calculate_hedge_ratio
)

from app.analytics.spread import (
    calculate_spread
)

from app.analytics.zscore import (
    calculate_zscore
)

from app.utils.metrics import (
    calculate_sharpe_ratio,
    calculate_max_drawdown
)

class StatArbBacktester:

    def __init__(self):

        self.initial_capital = INITIAL_CAPITAL

        self.cash = INITIAL_CAPITAL

        self.trades = []

        self.equity_curve = [
            INITIAL_CAPITAL
        ]
    
    def download_pair_data(
        self,
        stock1,
        stock2,
        start,
        end
    ):

        df1 = yf.download(
            stock1,
            start=start,
            end=end,
            auto_adjust=True
        )

        df2 = yf.download(
            stock2,
            start=start,
            end=end,
            auto_adjust=True
        )

        data = pd.DataFrame()

        data["x"] = df1["Close"]

        data["y"] = df2["Close"]

        data.dropna(inplace=True)

        return data
    
    
    def run_pair(
        self,
        stock1,
        stock2,
        start,
        end
    ):

        df = self.download_pair_data(
            stock1,
            stock2,
            start,
            end
        )

        position = None

        for i in range(
            LOOKBACK_WINDOW,
            len(df)
        ):

            window = df.iloc[
                i-LOOKBACK_WINDOW:i
            ]

            x = window["x"].values

            y = window["y"].values

            beta = calculate_hedge_ratio(
                x,
                y
            )

            spread = calculate_spread(
                x,
                y,
                beta
            )

            zscore = calculate_zscore(
                spread
            )

            price_x = df.iloc[i]["x"]

            price_y = df.iloc[i]["y"]
            
            if position is None:

                if zscore > ENTRY_ZSCORE:

                    position = {

                        "type":
                            "SHORT_SPREAD",

                        "entry_x":
                            price_x,

                        "entry_y":
                            price_y,

                        "beta":
                            beta
                    }

                elif zscore < -ENTRY_ZSCORE:

                    position = {

                        "type":
                            "LONG_SPREAD",

                        "entry_x":
                            price_x,

                        "entry_y":
                            price_y,

                        "beta":
                            beta
                    }
            elif abs(zscore) < EXIT_ZSCORE:

                beta = position["beta"]

                entry_x = position["entry_x"]

                entry_y = position["entry_y"]

                if position["type"] == "LONG_SPREAD":

                    pnl = (

                        (price_y - entry_y)

                        -

                        beta *

                        (price_x - entry_x)

                    )

                else:

                    pnl = (

                        (entry_y - price_y)

                        -

                        beta *

                        (entry_x - price_x)

                    )

                self.cash += pnl

                self.equity_curve.append(
                    self.cash
                )

                self.trades.append({

                    "pair":
                        f"{stock1}-{stock2}",

                    "pnl":
                        round(
                            pnl,
                            2
                        )
                })

                position = None
                
    
    def run_portfolio(
        self,
        start,
        end
    ):

        for pair in PAIRS:

            stock1 = pair[0]

            stock2 = pair[1]

            print(
                f"Running {stock1}-{stock2}"
            )

            self.run_pair(

                stock1,

                stock2,

                start,

                end
            )

        return self.generate_report()
    
    
    
    def generate_report(self):

        total_return = (

            self.cash

            -

            self.initial_capital

        )

        return_pct = (

            total_return

            /

            self.initial_capital

        ) * 100

        wins = len(

            [

                t

                for t in self.trades

                if t["pnl"] > 0

            ]

        )

        win_rate = 0

        if len(self.trades):

            win_rate = (

                wins

                /

                len(self.trades)

            ) * 100

        report = {

            "initial_capital":
                round(
                    self.initial_capital,
                    2
                ),

            "final_capital":
                round(
                    self.cash,
                    2
                ),

            "total_return":
                round(
                    total_return,
                    2
                ),

            "return_pct":
                round(
                    return_pct,
                    2
                ),

            "total_trades":
                len(
                    self.trades
                ),

            "win_rate":
                round(
                    win_rate,
                    2
                ),

            "sharpe_ratio":
                round(
                    calculate_sharpe_ratio(
                        self.equity_curve
                    ),
                    2
                ),

            "max_drawdown":
                round(
                    calculate_max_drawdown(
                        self.equity_curve
                    ),
                    2
                )
        }

        return report
    
if __name__ == "__main__":

    bt = StatArbBacktester()

    report = bt.run_portfolio(

        start="2020-01-01",

        end="2025-01-01"
    )

    print(report)