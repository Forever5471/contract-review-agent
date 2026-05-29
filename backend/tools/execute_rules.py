from __future__ import annotations

import re
from typing import Any

from ..rules import list_rules
from .local_rag import LocalRagTool


class RuleEngineTool:
    name = "RuleEngineTool"
    version = "0.3.0"

    def __init__(self, rag: LocalRagTool, llm: Any | None = None, agent_config: dict[str, Any] | None = None) -> None:
        self.rag = rag
        self.llm = llm
        self.agent_config = agent_config or {}

    def run(
        self,
        text: str,
        contract_type: str,
        fields: dict[str, Any],
        clauses: list[dict[str, Any]] | None = None,
        strategy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        risks = []
        rule_events = []
        warnings = []
        rules = list_rules(include_disabled=False)
        strategy_rule_ids = self._strategy_rule_ids(strategy)
        if strategy_rule_ids:
            rules_by_id = {rule["id"]: rule for rule in rules}
            missing_rule_ids = [rule_id for rule_id in strategy_rule_ids if rule_id not in rules_by_id]
            rules = [rules_by_id[rule_id] for rule_id in strategy_rule_ids if rule_id in rules_by_id]
            if missing_rule_ids:
                warnings.append(f"审核策略关联的规则不存在或未启用：{', '.join(missing_rule_ids)}")
        for rule in rules:
            result = self._evaluate_rule(rule, text, contract_type, fields, clauses or [])
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
                "executed_rules": len(rules),
                "risks": risks,
                "rule_events": rule_events,
                "llm_enabled": self.llm is not None,
                "llm_provider": getattr(getattr(self.llm, "config", None), "provider", None) if self.llm is not None else None,
                "llm_model": getattr(self.llm, "model", None),
                "confidence_detail": confidence_detail,
                "review_strategy": self._strategy_summary(strategy, rules),
            },
            "evidence": [item for risk in risks for item in risk.get("evidence", [])][:20],
            "warnings": warnings,
        }

    def _strategy_rule_ids(self, strategy: dict[str, Any] | None) -> list[str]:
        if not strategy:
            return []
        rule_ids = strategy.get("rule_ids") or []
        return [str(rule_id).strip() for rule_id in rule_ids if str(rule_id).strip()]

    def _strategy_summary(self, strategy: dict[str, Any] | None, executed_rules: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not strategy:
            return None
        return {
            "id": strategy.get("id"),
            "name": strategy.get("name"),
            "template_type": strategy.get("template_type"),
            "description": strategy.get("description"),
            "agent_instruction": strategy.get("agent_instruction"),
            "rule_ids": self._strategy_rule_ids(strategy),
            "executed_rule_ids": [rule.get("id") for rule in executed_rules],
        }

    def run_one(
        self,
        rule: dict[str, Any],
        text: str,
        contract_type: str,
        fields: dict[str, Any],
        clauses: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        result = self._evaluate_rule(rule, text, contract_type, fields, clauses or [])
        confidence_detail = self._calculate_confidence([result], [] if result["passed"] else [result], fields, result.get("warnings", []))
        return {
            "tool_name": self.name,
            "tool_version": self.version,
            "status": "success",
            "confidence": confidence_detail["overall"],
            "data": {
                "rule_event": result,
                "risks": [] if result["passed"] else [result],
                "llm_enabled": self.llm is not None,
                "llm_provider": getattr(getattr(self.llm, "config", None), "provider", None) if self.llm is not None else None,
                "llm_model": getattr(self.llm, "model", None),
                "confidence_detail": confidence_detail,
            },
            "evidence": result.get("evidence", [])[:20],
            "warnings": result.get("warnings", []),
        }

    def _evaluate_rule(
        self,
        rule: dict[str, Any],
        text: str,
        contract_type: str,
        fields: dict[str, Any],
        clauses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        rule_id = rule["id"]
        passed = True
        issue = ""
        suggestion = ""
        evidence: list[dict[str, Any]] = []
        warnings: list[str] = []
        llm_used = False
        llm_meta: dict[str, Any] = {}
        relevant_clauses = self._match_relevant_clauses(rule, clauses)
        input_result = self._extract_rule_inputs(rule, text, contract_type, fields, relevant_clauses)
        rule_inputs = input_result["values"]
        warnings.extend(input_result.get("warnings", []))

        if rule["mode"] == "脚本模式":
            script_result = self._evaluate_script_rule(rule, text, contract_type, fields, rule_inputs, relevant_clauses)
            if script_result.get("error"):
                passed = False
                issue = f"规则脚本执行失败：{script_result['error']}"
                suggestion = "请在规则配置中修正 Python 脚本后重新审核。"
                warnings.append(f"{rule_id} 脚本执行失败：{script_result['error']}")
            elif script_result.get("missing_script"):
                passed = False
                issue = "规则未配置 Python 脚本。"
                suggestion = "请在规则配置中补充脚本后重新审核。"
                warnings.append(f"{rule_id} 脚本模式未配置脚本。")
            else:
                passed = bool(script_result.get("passed", True))
                issue = str(script_result.get("issue") or "").strip()
                suggestion = str(script_result.get("suggestion") or "").strip()
                evidence = script_result.get("evidence") or []
        elif rule["mode"] == "指令模式":
            evidence = self._build_instruction_evidence(rule, relevant_clauses)
            fallback_judgement = {"passed": passed, "issue": issue, "suggestion": suggestion}
            llm_result = self._evaluate_instruction_rule(
                rule=rule,
                text=text,
                contract_type=contract_type,
                fields=fields,
                clauses=relevant_clauses,
                rule_inputs=rule_inputs,
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
                passed = False
                issue = f"指令模式暂未完成判断：{llm_result['error']}"
                suggestion = "请确认 LLM 已配置，或切换到脚本模式后使用 Python 脚本判断。"
                warnings.append(f"{rule_id} 指令模式 LLM 调用未生效：{llm_result['error']}")

        if not passed:
            source_excerpt = self._find_source_excerpt(rule, text, evidence, rule_inputs, relevant_clauses)
            if source_excerpt:
                evidence = [{"type": "source_excerpt", "snippet": source_excerpt}, *evidence]

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
            "matched_clauses": [
                {
                    "id": clause.get("id"),
                    "number": clause.get("number"),
                    "title": clause.get("title"),
                    "type": clause.get("type"),
                    "location": clause.get("location"),
                    "text": str(clause.get("text") or "")[:500],
                }
                for clause in relevant_clauses[:5]
            ],
            "rule_inputs": rule_inputs,
            "input_extraction": input_result.get("meta", {}),
            **llm_meta,
        }

    def _match_relevant_clauses(self, rule: dict[str, Any], clauses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not clauses:
            return []
        query_parts = [
            rule.get("id", ""),
            rule.get("name", ""),
            rule.get("description", ""),
            rule.get("instruction", ""),
            " ".join(rule.get("scope") or []),
            " ".join(str(param.get("description") or param.get("display_name") or "") for param in rule.get("input_params", [])),
        ]
        query = " ".join(query_parts)
        terms = self._rule_keywords(rule)
        scored = []
        for clause in clauses:
            haystack = f"{clause.get('title', '')} {clause.get('type', '')} {clause.get('text', '')}"
            score = 0
            for term in terms:
                if term and term in haystack:
                    score += 3 if term in str(clause.get("title", "")) else 1
            for token in re.findall(r"[\u4e00-\u9fa5]{2,}|[A-Za-z0-9_]{2,}", query):
                if token in haystack:
                    score += 0.4
            if score > 0:
                scored.append((score, clause))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [clause for _, clause in scored[:6]]

    def _rule_keywords(self, rule: dict[str, Any]) -> list[str]:
        keyword_map = {
            "SL-GEN-003": ["甲方", "乙方", "供货人", "收货人", "主体", "签章页"],
            "SL-GEN-004": ["甲方", "乙方", "洛阳盛龙", "盛龙矿业", "供货人"],
            "SL-GEN-010": ["付款", "支付", "发票", "税率", "结算"],
            "SL-GEN-012": ["生效前支付", "签订前支付", "审批前支付", "付款"],
            "SL-GEN-014": ["签字", "盖章", "生效", "签章"],
            "SL-ROLE-OFFICE-001": ["合同总价", "金额", "价款", "审批"],
            "SL-TYPE-ENG-002": ["工程", "施工", "安全", "外包"],
            "SL-ROLE-LEGAL-002": ["违约", "违约金", "解除", "赔偿"],
        }
        text = " ".join(
            str(item or "")
            for item in [
                rule.get("name"),
                rule.get("description"),
                rule.get("instruction"),
                " ".join(rule.get("scope") or []),
            ]
        )
        terms = set(keyword_map.get(rule.get("id"), []))
        terms.update(re.findall(r"[\u4e00-\u9fa5]{2,}|[A-Za-z0-9_]{2,}", text))
        return [term for term in terms if len(term) >= 2]

    def _param_looks_like_clause(self, name: str, description: str) -> bool:
        haystack = f"{name} {description}"
        return any(keyword in haystack for keyword in ["条款", "原文", "约定", "付款", "发票", "违约", "签章", "生效", "安全"])

    def _clause_briefs(self, clauses: list[dict[str, Any]], limit: int = 6) -> list[dict[str, Any]]:
        return [
            {
                "id": clause.get("id"),
                "number": clause.get("number"),
                "title": clause.get("title"),
                "type": clause.get("type"),
                "location": clause.get("location"),
                "text": str(clause.get("text") or "")[:900],
            }
            for clause in clauses[:limit]
        ]

    def _find_source_excerpt(
        self,
        rule: dict[str, Any],
        text: str,
        evidence: list[dict[str, Any]],
        rule_inputs: dict[str, Any],
        relevant_clauses: list[dict[str, Any]] | None = None,
    ) -> str:
        for item in evidence:
            snippet = str(item.get("snippet") or "").strip()
            if snippet:
                return snippet
        for clause in relevant_clauses or []:
            clause_text = str(clause.get("text") or "").strip()
            if clause_text:
                return clause_text[:500]

        candidates: list[str] = []
        for value in rule_inputs.values():
            if isinstance(value, str) and value.strip():
                candidates.append(value.strip())
            elif isinstance(value, list):
                candidates.extend(str(item).strip() for item in value if str(item).strip())

        keyword_map = {
            "SL-GEN-003": ["甲方", "乙方", "供货人", "收货人", "主体", "签章页"],
            "SL-GEN-004": ["甲方", "乙方", "洛阳盛龙", "盛龙矿业", "供货人"],
            "SL-GEN-010": ["付款", "支付", "发票", "税率", "结算"],
            "SL-GEN-012": ["生效前支付", "签订前支付", "审批前支付", "付款"],
            "SL-GEN-014": ["签字", "盖章", "生效", "签章"],
            "SL-ROLE-OFFICE-001": ["合同总价", "金额", "价款"],
            "SL-TYPE-ENG-002": ["工程", "施工", "安全", "外包"],
            "SL-ROLE-LEGAL-002": ["违约", "违约金", "解除", "赔偿"],
        }
        candidates.extend(keyword_map.get(rule.get("id"), []))
        candidates.extend(str(item).strip() for item in rule.get("scope", []) if str(item).strip())

        normalized_text = text or ""
        for candidate in candidates:
            if len(candidate) < 2:
                continue
            index = normalized_text.find(candidate)
            if index >= 0:
                start = max(0, index - 90)
                end = min(len(normalized_text), index + len(candidate) + 180)
                return normalized_text[start:end].strip()
        return normalized_text[:260].strip()

    def _extract_rule_inputs(
        self,
        rule: dict[str, Any],
        text: str,
        contract_type: str,
        fields: dict[str, Any],
        relevant_clauses: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        params = [
            param
            for param in rule.get("input_params", [])
            if param.get("name") not in {"text", "fields", "contract_type", "rule", "rag", "re"}
        ]
        values = {param["name"]: self._fallback_param_value(param, text, contract_type, fields, relevant_clauses or []) for param in params}
        warnings: list[str] = []
        meta = {
            "method": "fallback_fields",
            "llm_used": False,
            "params": params,
        }
        if not params:
            return {"values": values, "warnings": warnings, "meta": meta}
        if self.llm is None:
            return {"values": values, "warnings": warnings, "meta": meta}

        llm_result = self._extract_rule_inputs_with_llm(rule, params, text, contract_type, fields, relevant_clauses or [])
        if llm_result.get("ok"):
            values.update(llm_result.get("values") or {})
            meta = {
                **meta,
                "method": "llm",
                "llm_used": True,
                "llm_provider": llm_result.get("provider"),
                "llm_model": llm_result.get("model"),
                "llm_request_id": llm_result.get("request_id"),
            }
        elif llm_result.get("error"):
            warnings.append(f"{rule['id']} 输入参数 LLM 抽取未生效，已使用系统字段和启发式抽取：{llm_result['error']}")
        return {"values": values, "warnings": warnings, "meta": meta}

    def _fallback_param_value(
        self,
        param: dict[str, Any],
        text: str,
        contract_type: str,
        fields: dict[str, Any],
        relevant_clauses: list[dict[str, Any]],
    ) -> Any:
        name = param.get("name")
        description = str(param.get("description") or param.get("display_name") or "")
        if name == "contract_type":
            return contract_type
        if name == "text":
            return text
        if name in fields:
            return self._coerce_param_value(fields.get(name), param.get("type"))
        alias_map = {
            "amount": "max_amount",
            "contract_amount": "max_amount",
            "total_amount": "max_amount",
            "parties": "parties",
            "party_names": "parties",
        }
        if name in alias_map and alias_map[name] in fields:
            return self._coerce_param_value(fields.get(alias_map[name]), param.get("type"))
        if relevant_clauses and self._param_looks_like_clause(name, description):
            clause_text = "\n\n".join(
                f"{clause.get('number', '')} {clause.get('title', '')}\n{clause.get('text', '')}"
                for clause in relevant_clauses[:4]
            ).strip()
            if param.get("type") == "array":
                return [clause.get("text", "") for clause in relevant_clauses[:4]]
            if param.get("type") == "object":
                return relevant_clauses[0]
            return clause_text
        if param.get("type") == "boolean":
            return self._fallback_boolean_by_description(description, text, fields)
        if param.get("type") == "number" and ("金额" in description or "价" in description):
            return fields.get("max_amount")
        if param.get("type") == "array":
            return []
        if param.get("type") == "object":
            return {}
        return ""

    def _fallback_boolean_by_description(self, description: str, text: str, fields: dict[str, Any]) -> bool:
        desc_map = [
            ("付款", "has_payment_clause"),
            ("支付", "has_payment_clause"),
            ("发票", "has_invoice_clause"),
            ("税率", "has_invoice_clause"),
            ("生效", "has_effective_clause"),
            ("签章", "has_seal_clause"),
            ("盖章", "has_seal_clause"),
            ("违约", "has_breach_clause"),
            ("安全", "has_safety_clause"),
            ("环保", "has_safety_clause"),
        ]
        for keyword, field_name in desc_map:
            if keyword in description and field_name in fields:
                return bool(fields.get(field_name))
        return any(keyword in text for keyword, _ in desc_map if keyword in description)

    def _extract_rule_inputs_with_llm(
        self,
        rule: dict[str, Any],
        params: list[dict[str, Any]],
        text: str,
        contract_type: str,
        fields: dict[str, Any],
        relevant_clauses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if self.llm is None:
            return {"ok": False, "error": "LLM 未配置"}
        payload = {
            "output_schema": {
                "values": {
                    param["name"]: {
                        "type": param.get("type", "string"),
                        "display_name": param.get("display_name", param["name"]),
                        "description": param.get("description", ""),
                    }
                    for param in params
                },
                "confidence": "number，0到1之间",
                "evidence_summary": "string，简述抽取依据",
            },
            "rule": {
                "id": rule.get("id"),
                "name": rule.get("name"),
                "description": rule.get("description"),
            },
            "contract": {
                "contract_type": contract_type,
                "fields": fields,
                "relevant_clauses": self._clause_briefs(relevant_clauses, limit=6),
                "text_excerpt": text[:9000],
            },
            "instructions": [
                "只从合同文本或结构化字段中抽取参数，不要编造。",
                "无法确定的 string 返回空字符串，number 返回 null，boolean 返回 false，array 返回空数组，object 返回空对象。",
                "只返回 JSON 对象。",
            ],
        }
        messages = [
            {
                "role": "system",
                "content": self._system_prompt(
                    "你是合同规则参数抽取器，根据参数定义从合同中抽取结构化值。只返回JSON对象。"
                ),
            },
            {"role": "user", "content": json_dumps(payload)},
        ]
        result = self.llm.complete_json(messages, request_id=f"{rule['id'].lower()}-inputs-{uuidish()}")
        if not result.get("ok"):
            return result
        raw_values = (result.get("json") or {}).get("values") or {}
        return {
            "ok": True,
            "provider": result.get("provider"),
            "model": result.get("model"),
            "request_id": result.get("request_id"),
            "values": {
                param["name"]: self._coerce_param_value(raw_values.get(param["name"]), param.get("type"))
                for param in params
            },
        }

    def _coerce_param_value(self, value: Any, param_type: str | None) -> Any:
        if param_type == "number":
            try:
                return None if value in {None, ""} else float(value)
            except (TypeError, ValueError):
                return None
        if param_type == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in {"true", "1", "yes", "y", "是", "有"}
            return bool(value)
        if param_type == "array":
            if isinstance(value, list):
                return value
            if value in {None, ""}:
                return []
            return [value]
        if param_type == "object":
            return value if isinstance(value, dict) else {}
        if value is None:
            return ""
        return str(value)

    def _build_instruction_evidence(self, rule: dict[str, Any], relevant_clauses: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        query = " ".join(
            item
            for item in [
                rule.get("name", ""),
                rule.get("description", ""),
                rule.get("instruction", ""),
                " ".join(rule.get("scope") or []),
            ]
            if item
        )
        clause_evidence = [
            {
                "type": "clause",
                "clause_id": clause.get("id"),
                "title": clause.get("title"),
                "clause_type": clause.get("type"),
                "location": clause.get("location"),
                "snippet": str(clause.get("text") or "")[:420],
            }
            for clause in (relevant_clauses or [])[:3]
        ]
        rag_evidence = self.rag.run(query, top_k=2)["data"]["results"] if query else []
        return [*clause_evidence, *rag_evidence]

    def _evaluate_script_rule(
        self,
        rule: dict[str, Any],
        text: str,
        contract_type: str,
        fields: dict[str, Any],
        rule_inputs: dict[str, Any],
        relevant_clauses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        script = str(rule.get("script") or "").strip()
        if not script:
            return {
                "passed": False,
                "issue": "",
                "suggestion": "",
                "evidence": [],
                "error": "",
                "missing_script": True,
            }

        safe_builtins = {
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "float": float,
            "int": int,
            "len": len,
            "list": list,
            "max": max,
            "min": min,
            "range": range,
            "round": round,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
        }
        env: dict[str, Any] = {
            "__builtins__": safe_builtins,
            "text": text,
            "contract_type": contract_type,
            "fields": fields,
            "clauses": relevant_clauses,
            "rule_inputs": rule_inputs,
            "rule": rule,
            "rag": self.rag,
            "re": re,
            "passed": True,
            "issue": "",
            "suggestion": "",
            "evidence": [],
        }
        env.update(rule_inputs)
        try:
            exec(compile(script, f"<rule {rule['id']}>", "exec"), env, env)
        except Exception as exc:
            return {"error": str(exc)}

        evidence = env.get("evidence") or []
        if not isinstance(evidence, list):
            evidence = [{"type": "script_value", "value": evidence}]
        return {
            "passed": bool(env.get("passed", True)),
            "issue": str(env.get("issue") or "").strip(),
            "suggestion": str(env.get("suggestion") or "").strip(),
            "evidence": evidence,
            "error": "",
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
        clauses: list[dict[str, Any]],
        rule_inputs: dict[str, Any],
        evidence: list[dict[str, Any]],
        fallback: dict[str, Any],
    ) -> dict[str, Any]:
        if self.llm is None:
            return {"ok": False, "error": "LLM 未配置"}

        messages = [
            {
                "role": "system",
                "content": (
                    self._system_prompt(
                        "你是合同审查规则执行器，只依据用户提供的合同文本、结构化字段、规则说明和RAG证据判断。"
                        "不要编造合同中不存在的事实，不输出思考过程。"
                        "只返回JSON对象，字段为 passed、issue、suggestion、confidence、evidence_summary。"
                    )
                ),
            },
            {
                "role": "user",
                "content": self._build_instruction_rule_payload(
                    rule,
                    text,
                    contract_type,
                    fields,
                    clauses,
                    evidence,
                    fallback,
                    rule_inputs,
                ),
            },
        ]
        result = self.llm.complete_json(messages, request_id=f"{rule['id'].lower()}-{uuidish()}")
        if not result.get("ok"):
            return result

        judgement = result.get("json") or {}
        if "passed" not in judgement:
            return {"ok": False, "error": "大模型 JSON 缺少 passed 字段。"}
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
        clauses: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
        fallback: dict[str, Any],
        rule_inputs: dict[str, Any] | None = None,
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
                "instruction": rule.get("instruction", ""),
                "input_params": rule.get("input_params", []),
                "output_params": rule.get("output_params", []),
            },
            "contract": {
                "contract_type": contract_type,
                "fields": fields,
                "clauses": self._clause_briefs(clauses, limit=8),
                "rule_inputs": rule_inputs or {},
                "text_excerpt": text[:7000],
            },
            "rag_evidence": evidence[:4],
            "fallback_judgement": fallback,
            "instructions": [
                str(self.agent_config.get("user_prompt") or ""),
                "如果合同文本证据不足以证明规则通过，应返回 passed=false。",
                "问题和建议要面向合同审核人员，简洁、可落地。",
                "不得引用输入以外的制度或事实。",
            ],
        }
        return json_dumps(payload)

    def _system_prompt(self, task_prompt: str) -> str:
        base = str(self.agent_config.get("system_prompt") or "").strip()
        return f"{base}\n\n{task_prompt}" if base else task_prompt


def json_dumps(value: Any) -> str:
    import json

    return json.dumps(value, ensure_ascii=False)


def uuidish() -> str:
    import uuid

    return uuid.uuid4().hex[:16]
