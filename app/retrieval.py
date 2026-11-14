"""Retrieval over risk-factor passages.

Baseline retriever: TF-IDF (1-2 grams) with cosine similarity. The interface is
deliberately small so an embedding + pgvector backend can replace it.
"""
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


@dataclass
class Hit:
    chunk: dict
    score: float


class TfidfRetriever:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
        self.matrix = self.vec.fit_transform([c["text"] for c in chunks])

    def search(self, query: str, k: int = 5, ticker: str | None = None,
               theme: str | None = None) -> list[Hit]:
        q = self.vec.transform([query])
        scores = linear_kernel(q, self.matrix).ravel()
        order = scores.argsort()[::-1]
        hits: list[Hit] = []
        for i in order:
            c = self.chunks[i]
            if ticker and c["ticker"] != ticker.upper():
                continue
            if theme and theme not in c["themes"]:
                continue
            hits.append(Hit(c, float(scores[i])))
            if len(hits) == k:
                break
        return hits
