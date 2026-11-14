from app.data import load_chunks, load_eval_queries
from app.eval import evaluate
from app.retrieval import TfidfRetriever


def test_obvious_query_ranks_expected_chunk_first():
    r = TfidfRetriever(load_chunks())
    assert r.search("ransomware attack hosting outage", k=1)[0].chunk["id"] == "VNTG-2"


def test_ticker_and_theme_filters_apply():
    r = TfidfRetriever(load_chunks())
    assert {h.chunk["ticker"] for h in r.search("risk", k=10, ticker="mrdn")} == {"MRDN"}
    assert all("cyber" in h.chunk["themes"] for h in r.search("breach", k=10, theme="cyber"))


def test_retrieval_quality_regression_gate():
    """Fails CI if retrieval quality drops below the measured baseline (small synthetic set)."""
    result = evaluate(TfidfRetriever(load_chunks()), load_eval_queries())
    assert result["recall@5"] >= 0.85
    assert result["mrr"] >= 0.80
