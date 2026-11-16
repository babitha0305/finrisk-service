"""SageMaker inference handler for the TF-IDF risk-factor retriever."""
import json
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


def model_fn(model_dir):
    with open(os.path.join(model_dir, "chunks.json"), encoding="utf-8") as f:
        chunks = json.load(f)
    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
    matrix = vec.fit_transform([c["text"] for c in chunks])
    return {"chunks": chunks, "vec": vec, "matrix": matrix}


def input_fn(body, content_type):
    if content_type != "application/json":
        raise ValueError(f"Unsupported content type: {content_type}")
    return json.loads(body)


def predict_fn(req, model):
    q = model["vec"].transform([req["q"]])
    scores = linear_kernel(q, model["matrix"]).ravel()
    k = int(req.get("k", 5))
    ticker = (req.get("ticker") or "").upper()
    theme = req.get("theme")
    hits = []
    for i in scores.argsort()[::-1]:
        c = model["chunks"][i]
        if ticker and c["ticker"] != ticker:
            continue
        if theme and theme not in c["themes"]:
            continue
        hits.append({"ticker": c["ticker"], "score": round(float(scores[i]), 4),
                     "themes": c["themes"], "text": c["text"]})
        if len(hits) == k:
            break
    return {"results": hits}


def output_fn(prediction, accept):
    return json.dumps(prediction), "application/json"
