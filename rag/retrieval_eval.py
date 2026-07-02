"""Simple retrieval evaluation for DocuFlow-Agent.

Run after building the vector database:
    python rag/retrieval_eval.py

The script only evaluates retrieval hit quality and latency. It does not call
the chat model, so it can be used to quickly debug chunk/top_k settings.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Allow running as `python rag/retrieval_eval.py` from project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.rag_service import RagSummarizeService  # noqa: E402
from utils.path_tool import get_abs_path  # noqa: E402


def load_eval_set(path: str | None = None) -> list[dict]:
    eval_path = Path(path or get_abs_path("eval/qa_eval_set.json"))
    return json.loads(eval_path.read_text(encoding="utf-8"))


def evaluate() -> dict:
    service = RagSummarizeService()
    dataset = load_eval_set()
    results = []
    total_latency = 0.0

    for item in dataset:
        question = item["question"]
        expected_keywords = item.get("expected_keywords", [])
        expected_source = item.get("expected_source", "")
        start = time.perf_counter()
        sources = service.get_retrieval_sources(question)
        latency = time.perf_counter() - start
        total_latency += latency

        retrieved_text = "\n".join([str(s.get("snippet", "")) for s in sources])
        retrieved_sources = "\n".join([str(s.get("source", "")) for s in sources])
        keyword_hit = any(keyword in retrieved_text for keyword in expected_keywords)
        source_hit = bool(expected_source and expected_source in retrieved_sources)
        hit = keyword_hit or source_hit
        results.append(
            {
                "question": question,
                "hit": hit,
                "keyword_hit": keyword_hit,
                "source_hit": source_hit,
                "latency_ms": round(latency * 1000, 2),
                "top_sources": [s.get("source", "") for s in sources],
            }
        )

    hit_count = sum(1 for result in results if result["hit"])
    metrics = {
        "total": len(results),
        "hit_count": hit_count,
        "hit_rate": round(hit_count / len(results), 4) if results else 0.0,
        "avg_latency_ms": round(total_latency * 1000 / len(results), 2) if results else 0.0,
        "results": results,
    }
    return metrics


if __name__ == "__main__":
    metrics = evaluate()
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
