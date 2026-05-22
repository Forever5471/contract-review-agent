from __future__ import annotations

from typing import Any


class TemplateMatchTool:
    name = "TemplateMatchTool"
    version = "0.2.0"

    def run(self, contract_type: str, text: str) -> dict[str, Any]:
        required_sections = ["合同", "价款", "付款", "违约", "争议", "签字", "盖章"]
        if "工程" in contract_type:
            required_sections += ["工期", "验收", "安全"]
        if "销售" in contract_type:
            required_sections += ["质量", "交货", "检验"]
        if "采购" in contract_type:
            required_sections += ["交货", "验收", "发票"]

        hits = [section for section in required_sections if section in text]
        missing = [section for section in required_sections if section not in hits]
        similarity = round(len(hits) / max(len(required_sections), 1), 2)
        confidence_detail = self._calculate_confidence(contract_type, similarity, len(hits), len(required_sections), bool(text))
        return {
            "tool_name": self.name,
            "tool_version": self.version,
            "status": "success",
            "confidence": confidence_detail["overall"],
            "data": {
                "template_name": f"{contract_type}标准模板",
                "similarity": similarity,
                "matched_sections": hits,
                "missing_sections": missing,
                "confidence_detail": confidence_detail,
            },
            "evidence": [{"type": "section", "value": item} for item in hits[:8]],
            "warnings": ["模板匹配度较低，建议人工复核。"] if similarity < 0.55 else [],
        }

    def _calculate_confidence(
        self,
        contract_type: str,
        similarity: float,
        hit_count: int,
        required_count: int,
        has_text: bool,
    ) -> dict[str, Any]:
        type_score = 0.45 if contract_type.startswith("未知") else 0.9
        coverage_score = similarity
        volume_score = min(1.0, hit_count / 5) if required_count else 0.0
        text_score = 1.0 if has_text else 0.0
        overall = type_score * 0.2 + coverage_score * 0.45 + volume_score * 0.25 + text_score * 0.1
        return {
            "overall": round(max(0.15, min(0.98, overall)), 2),
            "contract_type_confidence": round(type_score, 2),
            "section_coverage": round(coverage_score, 2),
            "matched_section_volume": round(volume_score, 2),
            "text_available": round(text_score, 2),
        }
