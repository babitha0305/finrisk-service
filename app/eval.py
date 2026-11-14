"""Retrieval evaluation: Recall@k and MRR against hand-labelled queries.

Run:  python -m app.eval
"""
import json
from pathlib import Path

from .data import load_chunks, load_eval_queries
from .retrieval import TfidfRetriever


def evaluate(retriever, queries: list[dict], ks=(1, 3, 5)) -> dict:
    hits_at = {k: 0 for k in ks}
    rr_sum = 0.0
    misses = []
    for item in queries:
        rel = set(item["relevant"])
        ranked = [h.chunk["id"] for h in retriever.search(item["query"], k=max(ks))]
        rank = next((i + 1 for i, cid in enumerate(ranked) if cid in rel), None)
        for k in ks:
            if rank is not None and rank <= k:
                hits_at[k] += 1
        rr_sum += 1.0 / rank if rank else 0.0
        if rank is None or rank > 1:
            misses.append({"query": item["query"], "relevant": sorted(rel), "top3": ranked[:3]})
    n = len(queries)
    return {"n_queries": n, **{f"recall@{k}": round(hits_at[k] / n, 4) for k in ks},
            "mrr": round(rr_sum / n, 4), "not_ranked_first": misses}


if __name__ == "__main__":
    result = evaluate(TfidfRetriever(load_chunks()), load_eval_queries())
    Path("eval_results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != "not_ranked_first"}, indent=2))
    print(f"{len(result['not_ranked_first'])} queries not ranked first (see eval_results.json)")
