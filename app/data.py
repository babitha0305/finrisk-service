"""Data loading. All bundled data is synthetic and uses fictional companies."""
import json
import os
from functools import lru_cache
from pathlib import Path

import pandas as pd

from .themes import tag_text

DATA_DIR = Path(os.environ.get("FINRISK_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))


@lru_cache(maxsize=1)
def load_chunks() -> list[dict]:
    with open(DATA_DIR / "risk_factors.json", encoding="utf-8") as f:
        chunks = json.load(f)
    for c in chunks:
        c["themes"] = tag_text(c["text"])
    return chunks


@lru_cache(maxsize=1)
def load_prices() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "prices.csv", parse_dates=["date"])
    return df.sort_values(["ticker", "date"]).reset_index(drop=True)


def load_eval_queries() -> list[dict]:
    with open(DATA_DIR / "eval_queries.json", encoding="utf-8") as f:
        return json.load(f)
