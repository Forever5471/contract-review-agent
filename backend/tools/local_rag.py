from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from ..document_utils import chunk_text, extract_text, normalize_text
from ..storage import WORKSPACE_DIR


class LocalRagTool:
    name = "LocalRagTool"
    version = "0.2.0"

    def __init__(self) -> None:
        self._index: list[dict[str, Any]] | None = None

    def run(self, query: str, top_k: int = 4) -> dict[str, Any]:
        index = self._ensure_index()
        terms = [term for term in query.replace("/", " ").replace("、", " ").split() if term]
        scored = []
        for item in index:
            score = self._score(item["text"], terms, query)
            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        results = [
            {
                "source": item["source"],
                "category": item["category"],
                "snippet": item["text"][:420],
                "score": round(score, 3),
            }
            for score, item in scored[:top_k]
        ]
        confidence_detail = self._calculate_confidence(results, len(index), top_k)
        return {
            "tool_name": self.name,
            "tool_version": self.version,
            "status": "success",
            "confidence": confidence_detail["overall"],
            "data": {"query": query, "results": results, "confidence_detail": confidence_detail},
            "evidence": results,
            "warnings": [] if results else ["未检索到强相关知识片段。"],
        }

    def _ensure_index(self) -> list[dict[str, Any]]:
        if self._index is not None:
            return self._index
        categories = ["规章制度", "合同模板", "历史合同"]
        items: list[dict[str, Any]] = []
        for category in categories:
            root = WORKSPACE_DIR / category
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in {".docx", ".doc", ".pdf", ".md", ".txt"}:
                    continue
                try:
                    text = extract_text(path, max_chars=45_000)
                except Exception:
                    text = ""
                if not text:
                    text = path.stem
                for chunk in chunk_text(text, size=900, overlap=100)[:20]:
                    items.append(
                        {
                            "category": category,
                            "source": str(path.relative_to(WORKSPACE_DIR)),
                            "text": normalize_text(chunk),
                        }
                    )
        self._index = items
        return items

    def _score(self, text: str, terms: list[str], query: str) -> float:
        if not text:
            return 0
        score = 0.0
        if query and query in text:
            score += 3.0
        for term in terms:
            if term and term in text:
                score += 1.0 + min(1.5, math.log(text.count(term) + 1))
        return score

    def _calculate_confidence(self, results: list[dict[str, Any]], index_size: int, top_k: int) -> dict[str, Any]:
        index_score = min(1.0, index_size / 120) if index_size else 0.0
        recall_score = min(1.0, len(results) / max(top_k, 1))
        top_score = min(1.0, (results[0]["score"] / 8.0)) if results else 0.0
        diversity_score = len({item["source"] for item in results}) / max(len(results), 1) if results else 0.0
        overall = index_score * 0.2 + recall_score * 0.3 + top_score * 0.35 + diversity_score * 0.15
        if not results:
            overall = min(0.3, index_score * 0.2)
        return {
            "overall": round(max(0.1, min(0.95, overall)), 2),
            "index_coverage": round(index_score, 2),
            "recall_count": round(recall_score, 2),
            "top_score_strength": round(top_score, 2),
            "source_diversity": round(diversity_score, 2),
        }
