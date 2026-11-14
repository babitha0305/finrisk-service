"""FastAPI service: risk-factor retrieval joined with market-risk analytics."""
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query, Response

from . import __version__
from .data import load_chunks, load_prices
from .monitoring import observe, record_search, render_metrics
from .retrieval import TfidfRetriever
from .risk import build_table

app = FastAPI(title="FinRisk Service", version=__version__)
app.middleware("http")(observe)


@lru_cache(maxsize=1)
def services():
    chunks = load_chunks()
    return TfidfRetriever(chunks), build_table(load_prices()), chunks


@app.get("/health")
def health():
    _, table, chunks = services()
    return {"status": "ok", "version": __version__, "chunks": len(chunks), "tickers": len(table)}


@app.get("/search")
def search(q: str = Query(..., min_length=3, max_length=300), k: int = Query(5, ge=1, le=20),
           ticker: str | None = None, theme: str | None = None):
    retriever, _, _ = services()
    hits = retriever.search(q, k=k, ticker=ticker, theme=theme)
    record_search(hits[0].score if hits else None)
    return {"query": q, "results": [
        {"id": h.chunk["id"], "ticker": h.chunk["ticker"], "company": h.chunk["company"],
         "score": round(h.score, 4), "themes": h.chunk["themes"], "text": h.chunk["text"]}
        for h in hits]}


@app.get("/risk/{ticker}")
def risk(ticker: str):
    _, table, _ = services()
    t = ticker.upper()
    if t not in table:
        raise HTTPException(404, f"unknown ticker {t}")
    return {"ticker": t, **table[t]}


@app.get("/screen")
def screen(theme: str | None = None, min_vol: float | None = Query(None, ge=0)):
    """Companies whose filings flag a risk theme, joined to realised volatility and VaR."""
    _, table, chunks = services()
    by_ticker: dict[str, set[str]] = {}
    names: dict[str, str] = {}
    for c in chunks:
        by_ticker.setdefault(c["ticker"], set()).update(c["themes"])
        names[c["ticker"]] = c["company"]
    rows = []
    for t, themes in by_ticker.items():
        if t not in table or (theme and theme not in themes):
            continue
        if min_vol is not None and table[t]["ann_volatility"] < min_vol:
            continue
        rows.append({"ticker": t, "company": names[t], "themes": sorted(themes),
                     "ann_volatility": round(table[t]["ann_volatility"], 4),
                     "var_95_1d": round(table[t]["var_95_1d"], 4)})
    return {"results": sorted(rows, key=lambda r: r["ann_volatility"], reverse=True)}


@app.get("/metrics")
def metrics():
    body, ctype = render_metrics()
    return Response(body, media_type=ctype)
