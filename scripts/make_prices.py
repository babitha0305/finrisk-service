"""Generate SYNTHETIC daily prices (seeded geometric Brownian motion) for the fictional tickers.

Replace data/prices.csv with real closes (columns: date,ticker,close) to use real data.
Run: python scripts/make_prices.py
"""
import numpy as np
import pandas as pd

SEED = 42
ANN_VOL = {"NWFR": .28, "HLXB": .55, "ORBS": .45, "MRDN": .25,
           "CBLT": .38, "LMNR": .30, "VNTG": .42, "ATLS": .22}
MU = 0.07
N_DAYS = 520

rng = np.random.default_rng(SEED)
dates = pd.bdate_range(end="2026-10-30", periods=N_DAYS)
rows = []
for ticker, vol in ANN_VOL.items():
    dt = 1 / 252
    shocks = rng.standard_normal(N_DAYS - 1)
    log_ret = (MU - 0.5 * vol**2) * dt + vol * np.sqrt(dt) * shocks
    close = 100 * np.exp(np.concatenate([[0], np.cumsum(log_ret)]))
    rows += [(d.date().isoformat(), ticker, round(float(c), 4)) for d, c in zip(dates, close)]
pd.DataFrame(rows, columns=["date", "ticker", "close"]).to_csv("data/prices.csv", index=False)
print(f"wrote data/prices.csv ({len(rows)} rows)")
