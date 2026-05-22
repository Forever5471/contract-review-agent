from __future__ import annotations

from pathlib import Path
from typing import Any

from ..document_utils import chunk_text, extract_text


class DocumentParseTool:
    name = "DocumentParseTool"
    version = "0.2.0"

    def run(self, file_path: str) -> dict[str, Any]:
        path = Path(file_path)
        text = extract_text(path, max_chars=120_000)
        chunks = chunk_text(text, size=1100, overlap=160)
        confidence_detail = self._calculate_confidence(path, text, len(chunks))
        return {
            "tool_name": self.name,
            "tool_version": self.version,
            "status": "success" if text else "warning",
            "confidence": confidence_detail["overall"],
            "data": {
                "file_name": path.name,
                "suffix": path.suffix.lower(),
                "text": text,
                "preview": text[:6000],
                "chunks": chunks[:80],
                "chunk_count": len(chunks),
                "confidence_detail": confidence_detail,
            },
            "evidence": [{"type": "file", "source": path.name}],
            "warnings": [] if text else ["暂未解析到有效文本，可能需要 OCR 或专用 Office 转换服务。"],
        }

    def _calculate_confidence(self, path: Path, text: str, chunk_count: int) -> dict[str, Any]:
        suffix_scores = {
            ".docx": 1.0,
            ".txt": 0.95,
            ".md": 0.95,
            ".pdf": 0.75,
            ".doc": 0.45,
        }
        suffix_score = suffix_scores.get(path.suffix.lower(), 0.25)
        text_length_score = min(1.0, len(text) / 3000) if text else 0.0
        chunk_score = min(1.0, chunk_count / 3) if chunk_count else 0.0
        preview_score = 1.0 if len(text[:6000]) >= min(len(text), 300) and text else 0.0
        overall = (
            suffix_score * 0.2
            + text_length_score * 0.45
            + chunk_score * 0.25
            + preview_score * 0.1
        )
        if not text:
            overall = min(overall, 0.2)
        return {
            "overall": round(max(0.15, min(0.98, overall)), 2),
            "suffix_support": round(suffix_score, 2),
            "text_length": round(text_length_score, 2),
            "chunk_coverage": round(chunk_score, 2),
            "preview_available": round(preview_score, 2),
        }
