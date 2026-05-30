# backend/app/strategies/base_strategy.py

from app.utils.metrics import (
    calculate_sharpe_ratio,
    calculate_max_drawdown
)


class BaseStrategy:

    def __init__(
        self,
        strategy_name: str,
        initial_capital: float = 100000
    ):

        self.strategy_name = strategy_name

        self.initial_capital = initial_capital
        self.current_capital = initial_capital

        self.cash = initial_capital

        self.positions = {}

        self.trade_history = []

        self.equity_curve = [
            initial_capital
        ]

        self.decisions_count = 0
        self.successful_decisions = 0

        self.gross_profit = 0
        self.gross_loss = 0

    # ---------------------------------------------------
    # Position Management
    # ---------------------------------------------------

    def open_position(
        self,
        pair_name,
        side,
        entry_price,
        quantity,
        zscore
    ):

        self.positions[pair_name] = {

            "side": side,

            "entry_price": entry_price,

            "quantity": quantity,

            "entry_zscore": zscore
        }

    def close_position(
        self,
        pair_name,
        exit_price,
        exit_zscore
    ):

        if pair_name not in self.positions:
            return None

        position = self.positions[pair_name]

        side = position["side"]

        qty = position["quantity"]

        entry_price = position["entry_price"]

        if side == "LONG":
            pnl = (
                exit_price - entry_price
            ) * qty

        else:
            pnl = (
                entry_price - exit_price
            ) * qty

        self.current_capital += pnl

        self.equity_curve.append(
            self.current_capital
        )

        self.decisions_count += 1

        if pnl > 0:

            self.successful_decisions += 1

            self.gross_profit += pnl

        else:

            self.gross_loss += abs(pnl)

        trade_record = {

            "pair": pair_name,

            "side": side,

            "entry_price": round(
                entry_price,
                4
            ),

            "exit_price": round(
                exit_price,
                4
            ),

            "entry_zscore": round(
                position["entry_zscore"],
                4
            ),

            "exit_zscore": round(
                exit_zscore,
                4
            ),

            "quantity": qty,

            "pnl": round(
                pnl,
                2
            )
        }

        self.trade_history.append(
            trade_record
        )

        del self.positions[pair_name]

        return trade_record

    # ---------------------------------------------------
    # Performance Metrics
    # ---------------------------------------------------

    def calculate_metrics(self):

        total_return = (
            self.current_capital
            - self.initial_capital
        )

        return_pct = (
            total_return
            / self.initial_capital
        ) * 100

        success_rate = 0

        if self.decisions_count > 0:

            success_rate = (
                self.successful_decisions
                / self.decisions_count
            ) * 100

        profit_factor = 0

        if self.gross_loss > 0:

            profit_factor = (
                self.gross_profit
                / self.gross_loss
            )

        return {

            "strategy_name":
                self.strategy_name,

            "initial_capital":
                round(
                    self.initial_capital,
                    2
                ),

            "final_capital":
                round(
                    self.current_capital,
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

            "metrics": {

                "total_trades":
                    self.decisions_count,

                "winning_trades":
                    self.successful_decisions,

                "win_rate":
                    round(
                        success_rate,
                        2
                    ),

                "profit_factor":
                    round(
                        profit_factor,
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
        }

