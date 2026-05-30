# backend/app/config.py

INITIAL_CAPITAL = 100000

LOOKBACK_WINDOW = 10

ENTRY_ZSCORE = 1.0
EXIT_ZSCORE = 0.5

PAIRS = [
    ("AAPL", "MSFT"),
    ("V", "MA"),
    ("KO", "PEP"),
    ("JPM", "BAC"),
    ("XOM", "CVX")
]

STOCK_UNIVERSE = list(
    set(
        [x for pair in PAIRS for x in pair]
    )
)