# backend/app/strategies/statistical_arbitrage.py

import asyncio
import numpy as np
import pandas as pd
import yfinance as yf

from app.config import (
    PAIRS,
    LOOKBACK_WINDOW,
    ENTRY_ZSCORE,
    EXIT_ZSCORE
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

from app.strategies.base_strategy import (
    BaseStrategy
)


class StatisticalArbitrage(BaseStrategy):

    def __init__(
        self,
        metrics_callback=None
    ):

        super().__init__(
            strategy_name="Statistical_Arbitrage_US"
        )

        self.pairs = PAIRS

        self.metrics_callback = metrics_callback

        self.price_history = {}

        for pair in self.pairs:

            self.price_history[pair] = {

                "x": [],
                "y": []
            }

    # --------------------------------------------------
    # START ENGINE
    # --------------------------------------------------
    async def start(self):

        print("[ENGINE START] Statistical Arbitrage Engine Online")
        print(f"Tracking {len(self.pairs)} pairs")

        while True:

            try:

                prices = self.fetch_market_data()

                for symbol, price in prices.items():

                    print(
                        f"[LIVE PRICE] "
                        f"{symbol} "
                        f"{round(price, 4)}"
                    )

                    await self.process_tick(
                        symbol,
                        price
                    )

            except Exception as e:

                print(
                    f"[ENGINE ERROR] {e}"
                )

            await asyncio.sleep(10)

    def fetch_market_data(self):

        symbols = sorted(
            set(
                [x for pair in self.pairs for x in pair]
            )
        )

        tickers = " ".join(symbols)

        df = yf.download(
            tickers=tickers,
            period="1d",
            interval="1m",
            group_by="ticker",
            auto_adjust=True,
            progress=False
        )

        prices = {}

        if df.empty:
            return prices

        if isinstance(df.columns, pd.MultiIndex):

            for symbol in symbols:

                if symbol not in df.columns.get_level_values(0):
                    continue

                series = df[symbol]["Close"].dropna()

                if series.empty:
                    continue

                prices[symbol] = float(
                    series.iloc[-1]
                )

        else:

            series = df["Close"].dropna()

            if not series.empty:

                prices[symbols[0]] = float(
                    series.iloc[-1]
                )

        return prices

    # --------------------------------------------------
    # PROCESS MARKET TICK
    # --------------------------------------------------
    async def process_tick(
        self,
        ticker,
        price
    ):

        for pair in self.pairs:

            x_symbol, y_symbol = pair

            history = self.price_history[pair]

            if ticker == x_symbol:

                history["x"].append(price)

            elif ticker == y_symbol:

                history["y"].append(price)

            if len(history["x"]) > LOOKBACK_WINDOW:
                history["x"].pop(0)

            if len(history["y"]) > LOOKBACK_WINDOW:
                history["y"].pop(0)

            if (
                len(history["x"])
                < LOOKBACK_WINDOW
            ):
                continue

            if (
                len(history["y"])
                < LOOKBACK_WINDOW
            ):
                continue

            await self.generate_signal(
                pair,
                history
            )
    
    # --------------------------------------------------
    # SIGNAL GENERATION
    # --------------------------------------------------
    async def generate_signal(
        self,
        pair,
        history
    ):

        x = np.array(history["x"])

        y = np.array(history["y"])

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

        pair_name = (
            f"{pair[0]}-{pair[1]}"
        )

        current_spread = spread[-1]

        print("\n")
        print(f"[PAIR] {pair_name}")
        print(f"[BETA] {round(beta, 4)}")
        print(f"[SPREAD] {round(current_spread, 4)}")
        print(f"[ZSCORE] {round(zscore, 4)}")

        await self.handle_signal(

            pair_name,

            current_spread,

            zscore
        )

    # --------------------------------------------------
    # TRADE LOGIC
    # --------------------------------------------------

    async def handle_signal(

        self,

        pair_name,

        spread,

        zscore
    ):

        # ----------------------------
        # ENTRY SHORT
        # ----------------------------

        if (

            zscore > ENTRY_ZSCORE

            and

            pair_name not in self.positions

        ):

            self.open_position(

                pair_name=pair_name,

                side="SHORT",

                entry_price=spread,

                quantity=100,

                zscore=zscore
            )

            print(
                f"[SHORT SIGNAL] "
                f"{pair_name}"
                f" | Z={round(zscore, 2)}"
            )

        # ----------------------------
        # ENTRY LONG
        # ----------------------------

        elif (

            zscore < -ENTRY_ZSCORE

            and

            pair_name not in self.positions

        ):

            self.open_position(

                pair_name=pair_name,

                side="LONG",

                entry_price=spread,

                quantity=100,

                zscore=zscore
            )

            print(
                f"[LONG SIGNAL] "
                f"{pair_name}"
                f" | Z={round(zscore, 2)}"
            )

        # ----------------------------
        # EXIT POSITION
        # ----------------------------

        elif (

            pair_name in self.positions

            and

            abs(zscore)

            < EXIT_ZSCORE

        ):

            trade = self.close_position(

                pair_name,

                spread,

                zscore
            )

            if trade:

                print(
                    f"[EXIT SIGNAL] "
                    f"{pair_name}"
                    f" | PnL={trade['pnl']}"
                )

        print("[PORTFOLIO]")
        print(f"Capital: {round(self.current_capital, 2)}")
        print(f"Trades: {self.decisions_count}")
        print(f"Open Positions: {len(self.positions)}")

        if self.metrics_callback:

            self.metrics_callback(
                self.calculate_metrics()
            )


if __name__ == "__main__":

    strategy = StatisticalArbitrage()

    asyncio.run(
        strategy.start()
    )