from __future__ import annotations

from typing import Any

from ..document_utils import find_keywords


CONTRACT_TYPES = [
    ("工程建设项目合同", ["工程", "施工", "承包", "建设", "竣工", "监理"]),
    ("工程安全管理协议", ["安全管理", "安全生产", "事故", "外包", "施工安全"]),
    ("矿石运输安全管理协议", ["运输", "车辆", "驾驶员", "矿石", "通行证"]),
    ("钼产品销售合同", ["销售", "钼", "氧化钼", "钼铁", "钼精矿", "需方", "供方"]),
    ("采购合同", ["采购", "买卖", "供货", "交货", "供应商", "验收"]),
    ("技术服务合同", ["技术服务", "服务范围", "成果交付", "咨询"]),
    ("借款/抵押/担保合同", ["借款", "抵押", "担保", "债权", "债务"]),
    ("股权/增资协议", ["股权", "增资", "扩股", "股东", "出资"]),
    ("资产转让合同", ["资产转让", "闲置", "报废", "转让价款"]),
]


class ContractClassifyTool:
    name = "ContractClassifyTool"
    version = "0.2.0"

    def run(self, text: str, file_name: str) -> dict[str, Any]:
        haystack = f"{file_name}\n{text[:5000]}"
        scored = []
        for contract_type, keywords in CONTRACT_TYPES:
            hits = find_keywords(haystack, keywords)
            if hits:
                scored.append((len(hits), contract_type, hits))
        scored.sort(reverse=True)
        if scored:
            score, contract_type, hits = scored[0]
        else:
            score, contract_type, hits = 0, "未知/通用合同", []
        confidence_detail = self._calculate_confidence(text, file_name, score, hits, scored)
        return {
            "tool_name": self.name,
            "tool_version": self.version,
            "status": "success",
            "confidence": confidence_detail["overall"],
            "data": {
                "contract_type": contract_type,
                "matched_keywords": hits,
                "confidence_detail": confidence_detail,
            },
            "evidence": [{"type": "keyword", "value": kw} for kw in hits],
            "warnings": [] if confidence_detail["overall"] >= 0.5 else ["合同类型置信度较低，建议人工确认。"],
        }

    def _calculate_confidence(
        self,
        text: str,
        file_name: str,
        best_score: int,
        hits: list[str],
        scored: list[tuple[int, str, list[str]]],
    ) -> dict[str, Any]:
        keyword_strength = min(1.0, best_score / 4)
        text_available = min(1.0, len(text) / 2500) if text else 0.0
        file_name_hits = sum(1 for hit in hits if hit and hit in file_name)
        file_name_signal = min(1.0, file_name_hits / 2)
        if len(scored) <= 1:
            ambiguity_score = 1.0
        else:
            top_score = scored[0][0]
            second_score = scored[1][0]
            ambiguity_score = min(1.0, max(0.0, (top_score - second_score + 1) / max(top_score, 1)))
        overall = (
            keyword_strength * 0.55
            + text_available * 0.15
            + file_name_signal * 0.10
            + ambiguity_score * 0.20
        )
        if best_score == 0:
            overall = text_available * 0.25 + file_name_signal * 0.15
        return {
            "overall": round(max(0.15, min(0.95, overall)), 2),
            "keyword_strength": round(keyword_strength, 2),
            "text_available": round(text_available, 2),
            "file_name_signal": round(file_name_signal, 2),
            "type_ambiguity": round(ambiguity_score, 2),
        }
