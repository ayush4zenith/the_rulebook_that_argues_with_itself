import json
import math
import string
from pathlib import Path
from typing import List, Dict, Tuple

INDEX_PATH = Path(__file__).parent.parent / "data" / "corpus_index.json"

# "student", "sgsits", "indore" are in the stoplist because they appear in almost
# every passage and would drown out the actually informative terms like "75%", "backlog", "hostel".
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "of", "in", "to",
    "for", "on", "at", "by", "with", "from", "that", "this", "these",
    "those", "it", "its", "and", "or", "but", "not", "as", "if", "then",
    "than", "so", "also", "i", "my", "me", "we", "our", "you", "your",
    "they", "their", "what", "which", "who", "when", "where", "how",
    "all", "any", "each", "no", "nor", "up", "into", "over", "under",
    "between", "about", "per", "such", "whether", "during", "while",
    "through", "only", "both", "either", "after", "before", "without",
    "within", "below", "above", "student", "students", "institute",
    "sgsits", "indore"
}


def tokenize(text: str) -> List[str]:
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return [t for t in text.split() if t and t not in STOPWORDS]


class BM25:
    """
    Standard BM25 ranking. k1 and b are the usual defaults from the literature.
    No external dependencies — this runs fully offline.
    """
    def __init__(self, chunks: List[Dict], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.corpus_tokens: List[List[str]] = []
        self.doc_freq: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.avgdl: float = 0.0
        self._build()

    def _build(self):
        for chunk in self.chunks:
            tokens = tokenize(chunk["text"])
            self.corpus_tokens.append(tokens)
            for tok in set(tokens):
                self.doc_freq[tok] = self.doc_freq.get(tok, 0) + 1

        N = len(self.chunks)
        self.avgdl = sum(len(t) for t in self.corpus_tokens) / max(N, 1)

        for term, df in self.doc_freq.items():
            self.idf[term] = math.log((N - df + 0.5) / (df + 0.5) + 1)

    def score(self, query: str, top_k: int = 8) -> List[Tuple[float, Dict]]:
        q_tokens = tokenize(query)
        scores = []

        for chunk, doc_tokens in zip(self.chunks, self.corpus_tokens):
            tf_map: Dict[str, int] = {}
            for t in doc_tokens:
                tf_map[t] = tf_map.get(t, 0) + 1

            dl = len(doc_tokens)
            score = 0.0
            for qt in q_tokens:
                if qt not in self.idf:
                    continue
                tf = tf_map.get(qt, 0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                score += self.idf[qt] * (numerator / denominator)

            scores.append((score, chunk))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [(s, c) for s, c in scores[:top_k] if s > 0.0]


# Singleton — BM25 index is built once on first call and reused across requests.
_bm25_instance: BM25 | None = None


def load_index() -> List[Dict]:
    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            f"Corpus index not found. Run: python engine/indexer.py"
        )
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_bm25() -> BM25:
    global _bm25_instance
    if _bm25_instance is None:
        _bm25_instance = BM25(load_index())
    return _bm25_instance


def retrieve(query: str, top_k: int = 8) -> List[Dict]:
    """Returns top_k passages ranked by BM25 relevance, with scores attached."""
    results = get_bm25().score(query, top_k=top_k)
    passages = []
    for score, chunk in results:
        p = dict(chunk)
        p["relevance_score"] = round(score, 4)
        passages.append(p)
    return passages


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "minimum attendance to sit exam"
    print(f"\nQuery: {query}\n" + "-" * 60)
    for p in retrieve(query, top_k=5):
        print(f"\n[{p['source']} | {p['section_hint']}] score={p['relevance_score']}")
        print(p["text"][:300], "...")
