from __future__ import annotations

from collections import Counter
from typing import Any


class ReportBuildTool:
    name = "ReportBuildTool"
    version = "0.2.0"

    def run(self, contract: dict[str, Any], risks: list[dict[str, Any]]) -> dict[str, Any]:
        counts = Counter(risk["priority"] for risk in risks)
        need_human = any(risk.get("need_human_confirm") for risk in risks)
        if any(risk["priority"] == "P0" for risk in risks):
            conclusion = "需退回/重点人工确认"
        elif any(risk["priority"] == "P1" for risk in risks):
            conclusion = "带高风险待确认"
        elif risks:
            conclusion = "存在一般风险，建议修订"
        else:
            conclusion = "未发现明显规则风险"

        report = {
            "conclusion": conclusion,
            "need_human_confirm": need_human,
            "risk_counts": {key: counts.get(key, 0) for key in ["P0", "P1", "P2", "P3"]},
            "summary": f"共命中 {len(risks)} 条风险，结论：{conclusion}。",
            "role_opinions": self._role_opinions(risks),
        }
        confidence_detail = self._calculate_confidence(report, risks)
        return {
            "tool_name": self.name,
            "tool_version": self.version,
            "status": "success",
            "confidence": confidence_detail["overall"],
            "data": {**report, "confidence_detail": confidence_detail},
            "evidence": [],
            "warnings": [],
        }

    def _role_opinions(self, risks: list[dict[str, Any]]) -> list[dict[str, str]]:
        buckets = {
            "业务/经办": [],
            "财务": [],
            "法务": [],
            "安全环保": [],
            "归口/用印": [],
        }
        for risk in risks:
            name = risk["rule_name"]
            if "付款" in name or "流程" in name:
                buckets["财务"].append(risk["issue"])
            if "违约" in name or "主体" in name:
                buckets["法务"].append(risk["issue"])
            if "安全" in name:
                buckets["安全环保"].append(risk["issue"])
            if "签章" in name or "流程" in name:
                buckets["归口/用印"].append(risk["issue"])
            buckets["业务/经办"].append(risk["issue"])
        return [
            {"role": role, "opinion": "；".join(items[:3]) if items else "暂未发现需该角色重点处理的问题。"}
            for role, items in buckets.items()
        ]

    def _calculate_confidence(self, report: dict[str, Any], risks: list[dict[str, Any]]) -> dict[str, Any]:
        if not risks:
            risk_structure = 1.0
        else:
            required = ["rule_id", "rule_name", "priority", "risk_level", "issue", "suggestion"]
            complete = 0
            for risk in risks:
                complete += sum(1 for key in required if risk.get(key)) / len(required)
            risk_structure = complete / len(risks)

        role_opinions = report.get("role_opinions") or []
        meaningful_roles = [
            item for item in role_opinions if item.get("opinion") and "暂未发现" not in item.get("opinion", "")
        ]
        role_coverage = len(meaningful_roles) / max(len(role_opinions), 1)

        counts = report.get("risk_counts") or {}
        count_consistency = 1.0 if sum(counts.get(key, 0) for key in ["P0", "P1", "P2", "P3"]) == len(risks) else 0.45

        summary = report.get("summary") or ""
        summary_quality = 0.35
        if report.get("conclusion") and report["conclusion"] in summary:
            summary_quality += 0.25
        if str(len(risks)) in summary:
            summary_quality += 0.2
        if 12 <= len(summary) <= 180:
            summary_quality += 0.2

        need_human_consistency = 1.0
        if any(risk.get("priority") in {"P0", "P1"} for risk in risks) and not report.get("need_human_confirm"):
            need_human_consistency = 0.4

        overall = (
            risk_structure * 0.35
            + role_coverage * 0.15
            + count_consistency * 0.2
            + summary_quality * 0.15
            + need_human_consistency * 0.15
        )
        return {
            "overall": round(max(0.2, min(0.98, overall)), 2),
            "risk_structure": round(risk_structure, 2),
            "role_coverage": round(role_coverage, 2),
            "count_consistency": round(count_consistency, 2),
            "summary_quality": round(summary_quality, 2),
            "human_confirm_consistency": round(need_human_consistency, 2),
        }
