from __future__ import annotations

import re
from typing import Any

from ..document_utils import normalize_text


class ClauseExtractTool:
    name = "ClauseExtractTool"
    version = "0.1.0"

    def run(self, text: str, contract_id: str = "") -> dict[str, Any]:
        clauses = self._extract_clauses(text or "", contract_id)
        confidence_detail = self._calculate_confidence(text or "", clauses)
        return {
            "tool_name": self.name,
            "tool_version": self.version,
            "status": "success" if clauses else "warning",
            "confidence": confidence_detail["overall"],
            "data": {
                "clauses": clauses,
                "clause_count": len(clauses),
                "confidence_detail": confidence_detail,
            },
            "evidence": [
                {
                    "type": "clause",
                    "clause_id": clause["id"],
                    "title": clause["title"],
                    "clause_type": clause["type"],
                }
                for clause in clauses[:12]
            ],
            "warnings": [] if clauses else ["暂未识别到稳定条款结构，后续审核将回退使用全文片段。"],
        }

    def _extract_clauses(self, text: str, contract_id: str) -> list[dict[str, Any]]:
        normalized = normalize_text(text)
        if not normalized:
            return []

        blocks = self._split_by_headings(normalized)
        if len(blocks) < 2:
            blocks = self._split_by_paragraphs(normalized)

        clauses = []
        for index, block in enumerate(blocks, start=1):
            content = block["text"].strip()
            if len(content) < 8:
                continue
            title = block.get("title") or self._infer_title(content)
            number = block.get("number") or str(index)
            char_start = normalized.find(content[: min(40, len(content))])
            if char_start < 0:
                char_start = block.get("char_start", 0)
            char_end = min(len(normalized), char_start + len(content))
            line_start = normalized[:char_start].count("\n") + 1
            line_end = normalized[:char_end].count("\n") + 1
            clauses.append(
                {
                    "id": f"CLAUSE-{len(clauses) + 1:03d}",
                    "number": number,
                    "title": title,
                    "type": self._classify_clause_type(title, content),
                    "text": content[:3000],
                    "contract_id": contract_id,
                    "page": None,
                    "position": {
                        "char_start": char_start,
                        "char_end": char_end,
                        "line_start": line_start,
                        "line_end": line_end,
                    },
                    "location": f"第{line_start}-{line_end}行",
                }
            )
        return clauses[:80]

    def _split_by_headings(self, text: str) -> list[dict[str, Any]]:
        heading_pattern = re.compile(
            r"(?m)^(?P<head>\s*(?P<number>(?:第[一二三四五六七八九十百千万0-9]+条)|(?:[一二三四五六七八九十]+、)|(?:[0-9]+[、.．]))\s*(?P<title>[^\n\r]{0,40}))$"
        )
        matches = list(heading_pattern.finditer(text))
        blocks = []
        for idx, match in enumerate(matches):
            start = match.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            segment = text[start:end].strip()
            if len(segment) < 10:
                continue
            title = self._clean_heading(match.group("title") or match.group("head") or "")
            blocks.append(
                {
                    "number": self._clean_heading(match.group("number") or str(idx + 1)),
                    "title": title or self._infer_title(segment),
                    "text": segment,
                    "char_start": start,
                }
            )
        return blocks

    def _split_by_paragraphs(self, text: str) -> list[dict[str, Any]]:
        paragraphs = [item.strip() for item in re.split(r"\n\s*\n|(?<=。)\s*(?=[一二三四五六七八九十]+、|[0-9]+[、.．])", text) if item.strip()]
        blocks = []
        buffer = ""
        for paragraph in paragraphs:
            if len(buffer) + len(paragraph) < 260:
                buffer = f"{buffer}\n{paragraph}".strip()
                continue
            if buffer:
                blocks.append({"text": buffer})
            buffer = paragraph
        if buffer:
            blocks.append({"text": buffer})
        return blocks[:80]

    def _infer_title(self, text: str) -> str:
        first_line = text.splitlines()[0].strip()
        first_line = re.sub(r"^(第[一二三四五六七八九十百千万0-9]+条|[一二三四五六七八九十]+、|[0-9]+[、.．])\s*", "", first_line)
        if 2 <= len(first_line) <= 24:
            return first_line
        clause_type = self._classify_clause_type("", text)
        return {
            "parties": "合同主体",
            "subject": "合同标的",
            "payment": "付款结算",
            "invoice": "发票税务",
            "delivery": "交付履行",
            "acceptance": "验收质量",
            "effective": "签章生效",
            "breach": "违约责任",
            "dispute": "争议解决",
            "safety": "安全环保",
            "confidentiality": "保密义务",
            "termination": "解除终止",
        }.get(clause_type, "其他条款")

    def _classify_clause_type(self, title: str, text: str) -> str:
        type_keywords = [
            ("subject", ["标的", "产品", "货物", "服务内容", "工程范围"]),
            ("delivery", ["交付", "交货", "发货", "运输", "履行"]),
            ("payment", ["付款", "支付", "价款", "结算", "收款", "账期"]),
            ("invoice", ["发票", "税率", "含税", "增值税", "开票"]),
            ("acceptance", ["验收", "质量", "检验", "合格", "质保"]),
            ("effective", ["生效", "签字", "盖章", "签章"]),
            ("breach", ["违约", "赔偿", "违约金", "解除权", "损失"]),
            ("dispute", ["争议", "仲裁", "诉讼", "管辖", "法院"]),
            ("safety", ["安全", "环保", "事故", "安全生产"]),
            ("confidentiality", ["保密", "商业秘密", "秘密信息"]),
            ("termination", ["解除", "终止", "提前终止"]),
            ("parties", ["甲方", "乙方", "供货人", "收货人", "委托方", "受托方", "主体"]),
        ]
        scores: dict[str, int] = {}
        for clause_type, keywords in type_keywords:
            score = 0
            for keyword in keywords:
                if keyword in title:
                    score += 4
                if keyword in text:
                    score += 1
            if clause_type == "parties" and not any(keyword in title for keyword in ["主体", "甲方", "乙方", "当事人"]):
                score = 0
            if score:
                scores[clause_type] = score
        if not scores:
            return "other"
        return max(scores.items(), key=lambda item: item[1])[0]

    def _clean_heading(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip(" ：:。.；;\t")

    def _calculate_confidence(self, text: str, clauses: list[dict[str, Any]]) -> dict[str, Any]:
        text_available = min(1.0, len(text) / 2500) if text else 0.0
        clause_coverage = min(1.0, len(clauses) / 8) if clauses else 0.0
        typed_count = sum(1 for clause in clauses if clause.get("type") != "other")
        type_coverage = typed_count / max(len(clauses), 1) if clauses else 0.0
        location_coverage = sum(1 for clause in clauses if clause.get("position")) / max(len(clauses), 1) if clauses else 0.0
        overall = text_available * 0.25 + clause_coverage * 0.35 + type_coverage * 0.25 + location_coverage * 0.15
        return {
            "overall": round(max(0.15, min(0.96, overall)), 2),
            "text_available": round(text_available, 2),
            "clause_coverage": round(clause_coverage, 2),
            "clause_type_coverage": round(type_coverage, 2),
            "location_coverage": round(location_coverage, 2),
        }
