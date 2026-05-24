from __future__ import annotations

from typing import Any

from ...llm import build_llm_client
from ...tools.build_report import ReportBuildTool


class ReviewReportingSkill:
    name = "ReviewReportingSkill"
    version = "0.5.0"

    def __init__(self, llm_client: Any | None = None, agent_config: dict[str, Any] | None = None) -> None:
        self.report_tool = ReportBuildTool()
        self.agent_config = agent_config or {}
        llm_tool_enabled = not self.agent_config or "LLMClient" in set(self.agent_config.get("tools") or [])
        self.llm_client = llm_client if llm_client is not None else (
            build_llm_client(self.agent_config.get("model")) if llm_tool_enabled else None
        )

    def run(self, contract: dict[str, Any], risks: list[dict[str, Any]]) -> dict[str, Any]:
        report_result = self.report_tool.run(contract, risks)
        report = dict(report_result["data"])
        warnings = list(report_result.get("warnings", []))
        llm_summary = self._polish_summary(contract, risks, report)
        if llm_summary["ok"]:
            report["summary"] = llm_summary["summary"]
            report["llm_summary_used"] = True
            report["llm_provider"] = llm_summary.get("provider")
            report["llm_model"] = llm_summary.get("model")
            report["llm_request_id"] = llm_summary.get("request_id")
            self._update_summary_confidence(report, llm_summary)
        else:
            report["llm_summary_used"] = False
            if llm_summary.get("error"):
                warnings.append(f"最终结果 GLM 润色未生效，已使用模板摘要：{llm_summary['error']}")

        human_opinion = self._draft_human_review_opinion(contract, risks, report)
        report["default_human_review_opinion"] = human_opinion["opinion"]
        report["default_human_review_opinion_source"] = human_opinion["source"]
        if human_opinion.get("provider"):
            report["human_opinion_llm_provider"] = human_opinion.get("provider")
            report["human_opinion_llm_model"] = human_opinion.get("model")
            report["human_opinion_llm_request_id"] = human_opinion.get("request_id")
        if human_opinion.get("error"):
            warnings.append(f"默认人工审核意见 GLM 生成未生效，已使用规则兜底意见：{human_opinion['error']}")

        confidence = self._calculate_skill_confidence(report, warnings)
        return {
            "skill_name": self.name,
            "skill_version": self.version,
            "status": report_result["status"],
            "confidence": confidence,
            "data": {
                **report,
                "tool_runs": [
                    {
                        "tool_name": report_result.get("tool_name"),
                        "tool_version": report_result.get("tool_version"),
                        "status": report_result.get("status"),
                        "confidence": confidence,
                        "base_confidence": report_result.get("confidence"),
                        "confidence_detail": report.get("confidence_detail"),
                        "llm_summary_used": report.get("llm_summary_used"),
                        "llm_provider": report.get("llm_provider"),
                        "llm_model": report.get("llm_model"),
                        "default_human_review_opinion_source": report.get("default_human_review_opinion_source"),
                        "warnings": report_result.get("warnings", []),
                    }
                ],
            },
            "evidence": report_result.get("evidence", []),
            "warnings": warnings,
        }

    def _update_summary_confidence(self, report: dict[str, Any], llm_summary: dict[str, Any]) -> None:
        detail = dict(report.get("confidence_detail") or {})
        summary = report.get("summary") or ""
        summary_quality = 0.0
        if 40 <= len(summary) <= 180:
            summary_quality += 0.30
        if report.get("conclusion") and report["conclusion"] in summary:
            summary_quality += 0.25
        risk_total = sum((report.get("risk_counts") or {}).values())
        if str(risk_total) in summary:
            summary_quality += 0.15
        if any(keyword in summary for keyword in ["人工确认", "人工审核", "再流转"]):
            summary_quality += 0.15
        if llm_summary.get("provider") and llm_summary.get("model"):
            summary_quality += 0.10
        if llm_summary.get("request_id"):
            summary_quality += 0.05
        detail["summary_quality"] = round(min(1.0, summary_quality), 2)
        detail["llm_summary_quality"] = round(
            min(
                1.0,
                (0.35 if llm_summary.get("provider") else 0.0)
                + (0.25 if llm_summary.get("model") else 0.0)
                + (0.25 if summary else 0.0)
                + (0.15 if llm_summary.get("request_id") else 0.0),
            ),
            2,
        )
        report["confidence_detail"] = detail

    def _calculate_skill_confidence(self, report: dict[str, Any], warnings: list[str]) -> float:
        detail = {**self._fallback_confidence_detail(report), **(report.get("confidence_detail") or {})}
        components = [
            float(detail["risk_structure"]) * 0.28,
            float(detail["role_coverage"]) * 0.12,
            float(detail["count_consistency"]) * 0.20,
            float(detail["summary_quality"]) * 0.20,
            float(detail["human_confirm_consistency"]) * 0.12,
            float(detail["llm_summary_quality"]) * 0.08,
        ]
        warning_penalty = min(0.15, len(warnings) * 0.05)
        return round(max(0.2, min(0.98, sum(components) - warning_penalty)), 2)

    def _fallback_confidence_detail(self, report: dict[str, Any]) -> dict[str, float]:
        counts = report.get("risk_counts") or {}
        count_values = [counts.get(key) for key in ["P0", "P1", "P2", "P3"]]
        valid_counts = all(isinstance(value, int) and value >= 0 for value in count_values)
        total_risks = sum(value for value in count_values if isinstance(value, int))

        role_opinions = report.get("role_opinions") or []
        meaningful_roles = [
            item
            for item in role_opinions
            if item.get("opinion") and "暂未发现" not in item.get("opinion", "")
        ]
        role_coverage = len(meaningful_roles) / max(len(role_opinions), 1) if role_opinions else 0.0

        summary = report.get("summary") or ""
        summary_quality = 0.0
        if summary:
            summary_quality += min(0.35, len(summary) / 180 * 0.35)
        if report.get("conclusion") and report["conclusion"] in summary:
            summary_quality += 0.25
        if str(total_risks) in summary:
            summary_quality += 0.20
        if total_risks == 0 or any(keyword in summary for keyword in ["风险", "确认", "修订", "通过"]):
            summary_quality += 0.20

        has_high_risk = bool((counts.get("P0") or 0) + (counts.get("P1") or 0))
        human_confirm_consistency = 1.0 if bool(report.get("need_human_confirm")) == has_high_risk else 0.0
        return {
            "risk_structure": 1.0 if valid_counts else 0.0,
            "role_coverage": round(role_coverage, 2),
            "count_consistency": 1.0 if valid_counts else 0.0,
            "summary_quality": round(min(1.0, summary_quality), 2),
            "human_confirm_consistency": human_confirm_consistency,
            "llm_summary_quality": self._fallback_llm_summary_quality(report),
        }

    def _fallback_llm_summary_quality(self, report: dict[str, Any]) -> float:
        return round(
            min(
                1.0,
                (0.30 if report.get("llm_summary_used") else 0.0)
                + (0.25 if report.get("llm_provider") else 0.0)
                + (0.25 if report.get("llm_model") else 0.0)
                + (0.20 if report.get("summary") else 0.0),
            ),
            2,
        )

    def _polish_summary(
        self,
        contract: dict[str, Any],
        risks: list[dict[str, Any]],
        report: dict[str, Any],
    ) -> dict[str, Any]:
        if self.llm_client is None:
            return {"ok": False, "error": ""}

        risk_briefs = [
            {
                "rule_id": risk.get("rule_id"),
                "rule_name": risk.get("rule_name"),
                "priority": risk.get("priority"),
                "issue": risk.get("issue"),
                "suggestion": risk.get("suggestion"),
            }
            for risk in risks
        ]
        messages = [
            {
                "role": "system",
                "content": self._system_prompt(
                    "你是合同智审报告助手。你只负责把已有审查结果润色成面向业务和客户的中文摘要，"
                    "不得新增风险，不得改变风险数量、优先级、结论和人工确认状态。"
                    "只返回JSON对象，字段为 summary。"
                ),
            },
            {
                "role": "user",
                "content": self._build_summary_prompt(contract, risk_briefs, report),
            },
        ]
        result = self.llm_client.complete_json(messages, request_id=f"report-{contract.get('id', '')[:20]}")
        if not result.get("ok"):
            return result

        summary = str((result.get("json") or {}).get("summary") or "").strip()
        if not summary:
            return {"ok": False, "error": "GLM JSON 缺少 summary 字段。"}
        return {
            "ok": True,
            "summary": summary[:260],
            "provider": result.get("provider"),
            "model": result.get("model"),
            "request_id": result.get("request_id"),
        }

    def _build_summary_prompt(
        self,
        contract: dict[str, Any],
        risk_briefs: list[dict[str, Any]],
        report: dict[str, Any],
    ) -> str:
        import json

        payload = {
            "output_schema": {
                "summary": "string，60到140字，适合展示在最终结果卡片中的中文摘要",
            },
            "contract": {
                "name": contract.get("name"),
                "contract_type": contract.get("contract_type"),
                "max_amount": (contract.get("fields") or {}).get("max_amount"),
            },
            "fixed_result": {
                "conclusion": report.get("conclusion"),
                "need_human_confirm": report.get("need_human_confirm"),
                "risk_counts": report.get("risk_counts"),
                "risk_total": len(risk_briefs),
            },
            "risks": risk_briefs,
            "instructions": [
                str(self.agent_config.get("user_prompt") or ""),
                "必须严格保留 fixed_result 中的结论、风险数量、风险等级分布和人工确认状态。",
                "摘要中的主要问题必须来自 risks 列表，不得套用样例问题或新增未命中的风险。",
                "如 need_human_confirm 为 true，结尾应提示相关人员人工确认后再流转；否则可提示按业务流程继续办理。",
                "只返回JSON，不要Markdown，不要项目符号。",
            ],
        }
        return json.dumps(payload, ensure_ascii=False)

    def _draft_human_review_opinion(
        self,
        contract: dict[str, Any],
        risks: list[dict[str, Any]],
        report: dict[str, Any],
    ) -> dict[str, Any]:
        fallback = self._fallback_human_review_opinion(contract, risks, report)
        if self.llm_client is None:
            return {"ok": False, "source": "template", "opinion": fallback, "error": ""}

        risk_briefs = [
            {
                "rule_id": risk.get("rule_id"),
                "rule_name": risk.get("rule_name"),
                "priority": risk.get("priority"),
                "risk_level": risk.get("risk_level"),
                "issue": risk.get("issue"),
                "suggestion": risk.get("suggestion"),
            }
            for risk in risks
        ]
        messages = [
            {
                "role": "system",
                "content": self._system_prompt(
                    "你是企业合同人工审核意见助手。你只根据合同智审智能体已经生成的最终报告、风险清单和修改建议，"
                    "起草一段可放入人工审核意见输入框的中文默认意见。"
                    "不得新增风险，不得改变审核结论，不得替人工做最终决策。只返回 JSON 对象，字段为 opinion。"
                ),
            },
            {
                "role": "user",
                "content": self._build_human_opinion_prompt(contract, risk_briefs, report),
            },
        ]
        result = self.llm_client.complete_json(messages, request_id=f"human-opinion-{contract.get('id', '')[:20]}")
        if not result.get("ok"):
            return {
                "ok": False,
                "source": "template",
                "opinion": fallback,
                "error": result.get("error", "GLM 调用失败"),
            }

        opinion = str((result.get("json") or {}).get("opinion") or "").strip()
        if not opinion:
            return {
                "ok": False,
                "source": "template",
                "opinion": fallback,
                "error": "GLM JSON 缺少 opinion 字段。",
            }
        return {
            "ok": True,
            "source": "glm",
            "opinion": opinion[:500],
            "provider": result.get("provider"),
            "model": result.get("model"),
            "request_id": result.get("request_id"),
        }

    def _build_human_opinion_prompt(
        self,
        contract: dict[str, Any],
        risk_briefs: list[dict[str, Any]],
        report: dict[str, Any],
    ) -> str:
        import json

        payload = {
            "output_schema": {
                "opinion": "string，80到220字，作为人工审核意见输入框的默认草稿，可被人工修改",
            },
            "contract": {
                "name": contract.get("name"),
                "contract_type": contract.get("contract_type"),
                "business_dept": contract.get("business_dept"),
                "initiator": contract.get("initiator"),
                "max_amount": (contract.get("fields") or {}).get("max_amount"),
            },
            "final_report": {
                "summary": report.get("summary"),
                "conclusion": report.get("conclusion"),
                "need_human_confirm": report.get("need_human_confirm"),
                "risk_counts": report.get("risk_counts"),
            },
            "risks": risk_briefs,
            "instructions": [
                str(self.agent_config.get("user_prompt") or ""),
                "用人工审核人的口吻起草，语气专业、可直接提交。",
                "若存在 P0/P1 风险，应明确建议补充或修订后再流转，不要直接写同意通过。",
                "若无风险，可写建议按制度完成用印和归档后通过。",
                "必须覆盖主要风险点和下一步处理动作，避免空泛表述。",
                "只返回 JSON，不要 Markdown，不要项目符号。",
            ],
        }
        return json.dumps(payload, ensure_ascii=False)

    def _fallback_human_review_opinion(
        self,
        contract: dict[str, Any],
        risks: list[dict[str, Any]],
        report: dict[str, Any],
    ) -> str:
        if not risks:
            return "经系统智能审核，当前合同未发现明显规则风险。建议经办部门复核合同正文、附件和签章信息后，按公司流程继续办理审批、用印和归档。"
        high_count = sum(1 for risk in risks if risk.get("priority") in {"P0", "P1"})
        risk_names = "、".join(str(risk.get("rule_name") or risk.get("rule_id") or "规则风险") for risk in risks[:3])
        action = "建议暂缓流转，先由经办部门会同法务、财务或用印相关人员补充修订后再提交复核。"
        if high_count == 0:
            action = "建议经办部门根据风险提示补充完善后，再按流程继续审批。"
        return (
            f"经系统智能审核，本合同共发现 {len(risks)} 项风险，其中高风险 {high_count} 项，"
            f"主要涉及{risk_names}。{action}"
        )

    def _system_prompt(self, task_prompt: str) -> str:
        base = str(self.agent_config.get("system_prompt") or "").strip()
        return f"{base}\n\n{task_prompt}" if base else task_prompt
