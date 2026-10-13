"""Semantic search over Acme's help articles (given in project 2, step 5).

This is the search you built by hand in the previous notebooks, packaged so other
notebooks can use it: embed every chunk once, stack the vectors into a matrix M,
then score a query against all chunks with one matrix-vector multiply (M @ q).
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np

from .acme import load_kb
from .llm import embed


def article_chunks() -> List[Dict]:
    """One chunk per help article: {"id": "KB05", "article": "KB05", "text": "title. text"}."""
    return [{"id": a["id"], "article": a["id"], "text": f"{a['title']}. {a['text']}"} for a in load_kb()]


class Index:
    def __init__(self, chunks: List[Dict]):
        self.chunks = chunks
        self.M = np.array(embed([c["text"] for c in chunks]), dtype=float)
        self.M /= np.linalg.norm(self.M, axis=1, keepdims=True)   # unit length: dot product = cosine

    def search(self, query: str, k: int = 3) -> List[Dict]:
        q = np.array(embed([query])[0], dtype=float)
        q /= np.linalg.norm(q)
        scores = self.M @ q
        top = np.argsort(-scores)[:k]
        return [dict(self.chunks[i], score=float(scores[i])) for i in top]
