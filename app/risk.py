"""Market-risk metrics from daily closes: volatility, historical VaR, drawdown."""
import numpy as np
import pandas as pd

TRADING_DAYS = 252


def compute_metrics(close: pd.Series) -> dict:
    close = close.dropna()
    if len(close) < 30:
        raise ValueError("need at least 30 observations")
    rets = close.pct_change().dropna()
    running_max = close.cummax()
    drawdown = ((running_max - close) / running_max).max()
    return {
        "n_obs": int(len(close)),
        "ann_volatility": float(rets.std(ddof=1) * np.sqrt(TRADING_DAYS)),
        # 1-day 95% historical VaR, reported as a positive loss fraction
        "var_95_1d": float(-np.percentile(rets, 5)),
        "max_drawdown": float(drawdown),
        "last_close": float(close.iloc[-1]),
    }


def build_table(prices: pd.DataFrame) -> dict[str, dict]:
    table = {}
    for ticker, g in prices.groupby("ticker"):
        m = compute_metrics(g.set_index("date")["close"])
        m["as_of"] = g["date"].max().date().isoformat()
        table[ticker] = m
    return table
