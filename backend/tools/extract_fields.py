from __future__ import annotations

import re
from typing import Any

from ..document_utils import extract_amounts


class FieldExtractTool:
    name = "FieldExtractTool"
    version = "0.2.0"

    def run(self, text: str) -> dict[str, Any]:
        amounts = extract_amounts(text)
        parties = self._extract_parties(text)
        fields = {
            "amounts": amounts,
            "max_amount": max(amounts) if amounts else None,
            "parties": parties,
            "has_payment_clause": any(kw in text for kw in ["付款", "支付", "结算", "价款"]),
            "has_invoice_clause": any(kw in text for kw in ["发票", "税率", "增值税", "含税"]),
            "has_effective_clause": any(kw in text for kw in ["生效", "签字", "盖章"]),
            "has_seal_clause": "盖章" in text or "公章" in text,
            "has_breach_clause": any(kw in text for kw in ["违约", "赔偿", "解除", "违约金"]),
            "has_safety_clause": any(kw in text for kw in ["安全", "安全生产", "事故", "环保"]),
        }
        confidence_detail = self._calculate_confidence(text, fields)
        evidence = []
        for key, value in fields.items():
            if isinstance(value, bool) and value:
                evidence.append({"type": "field", "field": key, "value": value})
        return {
            "tool_name": self.name,
            "tool_version": self.version,
            "status": "success",
            "confidence": confidence_detail["overall"],
            "data": {**fields, "confidence_detail": confidence_detail},
            "evidence": evidence,
            "warnings": [] if text else ["无可抽取文本。"],
        }

    def _extract_parties(self, text: str) -> list[str]:
        parties = []
        patterns = [
            r"(?:甲方|买方|委托方|发包方)[:：\s]*([^\n\r，,；;]{4,60})",
            r"(?:乙方|卖方|受托方|承包方)[:：\s]*([^\n\r，,；;]{4,60})",
        ]
        for pattern in patterns:
            for match in re.findall(pattern, text[:8000]):
                value = re.sub(r"\s+", "", match).strip()
                if value and value not in parties:
                    parties.append(value)
        return parties[:8]

    def _calculate_confidence(self, text: str, fields: dict[str, Any]) -> dict[str, Any]:
        text_score = min(1.0, len(text) / 2500) if text else 0.0
        party_score = min(1.0, len(fields.get("parties") or []) / 2)
        amount_score = 1.0 if fields.get("max_amount") is not None else 0.35
        clause_keys = [
            "has_payment_clause",
            "has_invoice_clause",
            "has_effective_clause",
            "has_seal_clause",
            "has_breach_clause",
            "has_safety_clause",
        ]
        clause_signal = sum(1 for key in clause_keys if fields.get(key)) / len(clause_keys)
        overall = text_score * 0.25 + party_score * 0.25 + amount_score * 0.20 + clause_signal * 0.30
        return {
            "overall": round(max(0.15, min(0.98, overall)), 2),
            "text_available": round(text_score, 2),
            "party_extraction": round(party_score, 2),
            "amount_extraction": round(amount_score, 2),
            "clause_signal": round(clause_signal, 2),
        }
