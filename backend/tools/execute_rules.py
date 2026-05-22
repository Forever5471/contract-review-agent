from __future__ import annotations

import re
from typing import Any

from ..rules import RULES
from .local_rag import LocalRagTool


class RuleEngineTool:
    name = "RuleEngineTool"
    version = "0.3.0"

    def __init__(self, rag: LocalRagTool, llm: Any | None = None) -> None:
        self.rag = rag
        self.llm = llm

    def run(self, text: str, contract_type: str, fields: dict[str, Any]) -> dict[str, Any]:
        risks = []
        rule_events = []
        warnings = []
        for rule in RULES:
            result = self._evaluate_rule(rule, text, contract_type, fields)
            rule_events.append(result)
            warnings.extend(result.get("warnings", []))
            if not result["passed"]:
                risks.append(result)
        confidence_detail = self._calculate_confidence(rule_events, risks, fields, warnings)
        return {
            "tool_name": self.name,
            "tool_version": self.version,
            "status": "success",
            "confidence": confidence_detail["overall"],
            "data": {
                "executed_rules": len(RULES),
                "risks": risks,
                "rule_events": rule_events,
                "llm_enabled": self.llm is not None,
                "llm_provider": "glm" if self.llm is not None else None,
                "llm_model": getattr(self.llm, "model", None),
                "confidence_detail": confidence_detail,
            },
            "evidence": [item for risk in risks for item in risk.get("evidence", [])][:20],
            "warnings": warnings,
        }

    def _evaluate_rule(
        self, rule: dict[str, Any], text: str, contract_type: str, fields: dict[str, Any]
    ) -> dict[str, Any]:
        rule_id = rule["id"]
        passed = True
        issue = ""
        suggestion = ""
        evidence: list[dict[str, Any]] = []
        warnings: list[str] = []
        llm_used = False
        llm_meta: dict[str, Any] = {}

        if rule_id == "SL-GEN-003":
            passed = len(fields.get("parties") or []) >= 2
            issue = "合同主体信息疑似不完整。"
            suggestion = "补充甲乙双方完整名称，并核对首页、正文和签章页一致性。"
            evidence = [{"type": "field", "field": "parties", "value": fields.get("parties", [])}]

        elif rule_id == "SL-GEN-004":
            our_keywords = ["盛龙矿业", "洛阳盛龙", "栾川龙宇", "龙宇钼业"]
            passed = any(keyword in text for keyword in our_keywords)
            issue = "未明显识别到我方主体名称，可能存在主体错误或非标准文本。"
            suggestion = "核对我方签约主体是否为授权主体，并确保签章主体一致。"
            evidence = [{"type": "keyword", "expected": our_keywords}]

        elif rule_id == "SL-GEN-010":
            passed = bool(fields.get("has_payment_clause")) and bool(fields.get("has_invoice_clause"))
            issue = "付款方式、付款条件或发票税率约定不完整。"
            suggestion = "明确付款节点、付款条件、发票类型、税率和结算资料要求。"
            evidence = self.rag.run("付款 条件 发票 税率 合同管理制度", top_k=2)["data"]["results"]

        elif rule_id == "SL-GEN-012":
            risky_patterns = ["生效前支付", "签订前支付", "审批前支付", "未生效前支付"]
            passed = not any(pattern in text for pattern in risky_patterns)
            issue = "发现付款可能早于合同生效或审批完成。"
            suggestion = "将付款条件调整为合同审批完成且双方签字盖章生效后支付。"
            evidence = [{"type": "pattern", "value": pattern} for pattern in risky_patterns if pattern in text]

        elif rule_id == "SL-GEN-014":
            passed = bool(fields.get("has_effective_clause")) and bool(fields.get("has_seal_clause"))
            issue = "签章或生效条款不完整。"
            suggestion = "补充“双方签字并盖章后生效”等明确表述。"
            evidence = [{"type": "field", "field": "has_effective_clause", "value": fields.get("has_effective_clause")}]

        elif rule_id == "SL-ROLE-OFFICE-001":
            amount = fields.get("max_amount") or 0
            passed = True
            if amount >= 100_000_000:
                issue = "合同金额达到 1 亿元以上，需会议评审和重点会签。"
                suggestion = "触发重要合同会议评审流程。"
                passed = False
            elif amount >= 300_000:
                issue = "合同金额达到重要合同阈值，需按重要合同流程审核。"
                suggestion = "触发重要合同审批和会签角色。"
                passed = False
            evidence = [{"type": "field", "field": "max_amount", "value": amount}]

        elif rule_id == "SL-TYPE-ENG-002":
            is_engineering = "工程" in contract_type or any(kw in text for kw in ["施工", "承包", "外包"])
            passed = (not is_engineering) or bool(fields.get("has_safety_clause"))
            issue = "工程/施工/外包类合同未明显关联安全管理责任或安全协议。"
            suggestion = "补充工程安全管理协议或明确安全生产责任、事故责任和保险要求。"
            evidence = self.rag.run("工程 安全 管理 协议 安全生产", top_k=2)["data"]["results"]

        elif rule_id == "SL-ROLE-LEGAL-002":
            passed = bool(fields.get("has_breach_clause")) and not re.search(r"依法承担.{0,8}责任", text)
            issue = "违约责任可能过于笼统，缺少量化标准或解除权。"
            suggestion = "明确违约情形、违约金计算方式、赔偿范围、解除权和维权费用承担。"
            evidence = self.rag.run("违约责任 违约金 解除权 赔偿 合同", top_k=2)["data"]["results"]

        if rule["mode"] == "指令模式":
            fallback_judgement = {"passed": passed, "issue": issue, "suggestion": suggestion}
            llm_result = self._evaluate_instruction_rule(
                rule=rule,
                text=text,
                contract_type=contract_type,
                fields=fields,
                evidence=evidence,
                fallback=fallback_judgement,
            )
            if llm_result["ok"]:
                judgement = llm_result["judgement"]
                passed = bool(judgement.get("passed", passed))
                issue = str(judgement.get("issue") or issue).strip()
                suggestion = str(judgement.get("suggestion") or suggestion).strip()
                llm_used = True
                llm_confidence = self._calculate_llm_judgement_confidence(judgement, fallback_judgement, evidence)
                llm_meta = {
                    "llm_provider": llm_result.get("provider"),
                    "llm_model": llm_result.get("model"),
                    "llm_request_id": llm_result.get("request_id"),
                    "llm_confidence": llm_confidence,
                }
                evidence = [
                    *evidence,
                    {
                        "type": "llm_judgement",
                        "provider": llm_result.get("provider"),
                        "model": llm_result.get("model"),
                        "request_id": llm_result.get("request_id"),
                        "summary": judgement.get("evidence_summary", ""),
                    },
                ]
            elif llm_result.get("error"):
                warnings.append(f"{rule_id} 指令模式 GLM 调用未生效，已回退脚本判断：{llm_result['error']}")

        return {
            "rule_id": rule_id,
            "rule_name": rule["name"],
            "mode": rule["mode"],
            "priority": rule["priority"],
            "risk_level": rule["risk_level"],
            "passed": passed,
            "issue": "" if passed else issue,
            "suggestion": "" if passed else suggestion,
            "need_human_confirm": (not passed and rule["priority"] in {"P0", "P1"}),
            "evidence": evidence,
            "warnings": warnings,
            "llm_used": llm_used,
            **llm_meta,
        }

    def _calculate_confidence(
        self,
        rule_events: list[dict[str, Any]],
        risks: list[dict[str, Any]],
        fields: dict[str, Any],
        warnings: list[str],
    ) -> dict[str, Any]:
        field_keys = [
            "parties",
            "max_amount",
            "has_payment_clause",
            "has_invoice_clause",
            "has_effective_clause",
            "has_seal_clause",
            "has_breach_clause",
            "has_safety_clause",
        ]
        filled_fields = 0
        for key in field_keys:
            value = fields.get(key)
            if isinstance(value, list):
                filled_fields += 1 if value else 0
            elif value is not None:
                filled_fields += 1
        field_completeness = filled_fields / len(field_keys)

        if rule_events:
            deterministic_count = sum(1 for event in rule_events if event.get("mode") == "脚本模式")
            script_confidence = deterministic_count / len(rule_events)
        else:
            script_confidence = 0.0

        evidence_bearing = [event for event in rule_events if event.get("evidence")]
        evidence_support = len(evidence_bearing) / max(len(rule_events), 1)

        instruction_events = [event for event in rule_events if event.get("mode") == "指令模式"]
        if instruction_events:
            llm_scores = [self._calculate_instruction_event_confidence(event) for event in instruction_events]
            llm_quality = sum(llm_scores) / len(llm_scores)
        else:
            llm_quality = 1.0

        warning_penalty = min(0.18, 0.04 * len(warnings))
        high_risk_penalty = min(0.08, 0.02 * sum(1 for risk in risks if risk.get("priority") in {"P0", "P1"}))

        overall = (
            field_completeness * 0.25
            + script_confidence * 0.25
            + evidence_support * 0.20
            + llm_quality * 0.20
            + (1.0 - warning_penalty - high_risk_penalty) * 0.10
        )
        overall = max(0.2, min(0.98, overall))
        return {
            "overall": round(overall, 2),
            "field_completeness": round(field_completeness, 2),
            "rule_determinism": round(script_confidence, 2),
            "evidence_support": round(evidence_support, 2),
            "llm_quality": round(llm_quality, 2),
            "warning_penalty": round(warning_penalty, 2),
            "risk_penalty": round(high_risk_penalty, 2),
        }

    def _calculate_instruction_event_confidence(self, event: dict[str, Any]) -> float:
        model_score = self._normalize_confidence(event.get("llm_confidence"))
        if model_score is not None:
            return model_score
        evidence_score = min(1.0, len(event.get("evidence") or []) / 2)
        if event.get("passed"):
            decision_completeness = 1.0
        else:
            decision_completeness = (
                (1.0 if event.get("issue") else 0.0) * 0.45
                + (1.0 if event.get("suggestion") else 0.0) * 0.45
                + (1.0 if event.get("rule_id") else 0.0) * 0.10
            )
        warning_score = max(0.0, 1.0 - len(event.get("warnings") or []) * 0.25)
        return round(
            max(
                0.2,
                min(
                    0.9,
                    evidence_score * 0.35 + decision_completeness * 0.45 + warning_score * 0.20,
                ),
            ),
            2,
        )

    def _calculate_llm_judgement_confidence(
        self,
        judgement: dict[str, Any],
        fallback: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> float:
        model_score = self._normalize_confidence(judgement.get("confidence"))
        passed = bool(judgement.get("passed"))
        issue = str(judgement.get("issue") or "").strip()
        suggestion = str(judgement.get("suggestion") or "").strip()
        summary = str(judgement.get("evidence_summary") or "").strip()

        decision_score = 1.0 if "passed" in judgement else 0.0
        issue_score = 1.0 if passed or issue else 0.0
        suggestion_score = 1.0 if passed or suggestion else 0.0
        summary_score = min(1.0, len(summary) / 24) if summary else 0.0
        evidence_score = min(1.0, len(evidence) / 2) if evidence else 0.0
        fallback_alignment = 1.0 if passed == bool(fallback.get("passed")) else 0.65

        structural_score = (
            decision_score * 0.25
            + issue_score * 0.20
            + suggestion_score * 0.20
            + summary_score * 0.20
            + evidence_score * 0.10
            + fallback_alignment * 0.05
        )
        if model_score is None:
            combined = structural_score
        else:
            combined = model_score * 0.60 + structural_score * 0.40
        return round(max(0.2, min(0.98, combined)), 2)

    def _normalize_confidence(self, value: Any) -> float | None:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return None
        if 1 < score <= 100:
            score = score / 100
        return max(0.0, min(1.0, score))

    def _evaluate_instruction_rule(
        self,
        rule: dict[str, Any],
        text: str,
        contract_type: str,
        fields: dict[str, Any],
        evidence: list[dict[str, Any]],
        fallback: dict[str, Any],
    ) -> dict[str, Any]:
        if self.llm is None:
            return {"ok": False, "error": ""}

        messages = [
            {
                "role": "system",
                "content": (
                    "你是合同审查规则执行器，只依据用户提供的合同文本、结构化字段、规则说明和RAG证据判断。"
                    "不要编造合同中不存在的事实，不输出思考过程。"
                    "只返回JSON对象，字段为 passed、issue、suggestion、confidence、evidence_summary。"
                ),
            },
            {
                "role": "user",
                "content": self._build_instruction_rule_payload(rule, text, contract_type, fields, evidence, fallback),
            },
        ]
        result = self.llm.complete_json(messages, request_id=f"{rule['id'].lower()}-{uuidish()}")
        if not result.get("ok"):
            return result

        judgement = result.get("json") or {}
        if "passed" not in judgement:
            return {"ok": False, "error": "GLM JSON 缺少 passed 字段。"}
        return {
            "ok": True,
            "provider": result.get("provider"),
            "model": result.get("model"),
            "request_id": result.get("request_id"),
            "judgement": {
                "passed": bool(judgement.get("passed")),
                "issue": str(judgement.get("issue") or fallback.get("issue") or "").strip(),
                "suggestion": str(judgement.get("suggestion") or fallback.get("suggestion") or "").strip(),
                "confidence": judgement.get("confidence"),
                "evidence_summary": str(judgement.get("evidence_summary") or "").strip(),
            },
        }

    def _build_instruction_rule_payload(
        self,
        rule: dict[str, Any],
        text: str,
        contract_type: str,
        fields: dict[str, Any],
        evidence: list[dict[str, Any]],
        fallback: dict[str, Any],
    ) -> str:
        payload = {
            "output_schema": {
                "passed": "boolean，规则是否通过",
                "issue": "string，未通过时的问题描述；通过时为空字符串",
                "suggestion": "string，未通过时的修改建议；通过时为空字符串",
                "confidence": "number，0到1之间",
                "evidence_summary": "string，概括判断依据，必须来自输入材料",
            },
            "rule": {
                "id": rule["id"],
                "name": rule["name"],
                "mode": rule["mode"],
                "priority": rule["priority"],
                "risk_level": rule["risk_level"],
                "description": rule["description"],
            },
            "contract": {
                "contract_type": contract_type,
                "fields": fields,
                "text_excerpt": text[:7000],
            },
            "rag_evidence": evidence[:4],
            "fallback_judgement": fallback,
            "instructions": [
                "如果合同文本证据不足以证明规则通过，应返回 passed=false。",
                "问题和建议要面向合同审核人员，简洁、可落地。",
                "不得引用输入以外的制度或事实。",
            ],
        }
        return json_dumps(payload)


def json_dumps(value: Any) -> str:
    import json

    return json.dumps(value, ensure_ascii=False)


def uuidish() -> str:
    import uuid

    return uuid.uuid4().hex[:16]
