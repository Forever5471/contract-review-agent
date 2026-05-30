from __future__ import annotations

import traceback
from typing import Any

from .agent_configs import get_agent
from .agent_skills.contract_review import ContractReviewSkill
from .agent_skills.contract_understanding import ContractUnderstandingSkill
from .agent_skills.review_reporting import ReviewReportingSkill
from .flow_strategies import decide_contract_flow
from .llm import build_llm_client
from .storage import JsonStore
from .strategies import match_strategy


MAIN_AGENT_ID = "contract-review-main"

REQUIRED_REVIEW_SKILLS = [
    "ContractUnderstandingSkill",
    "ContractReviewSkill",
    "ReviewReportingSkill",
]

REQUIRED_TOOLS_BY_SKILL = {
    "ContractUnderstandingSkill": [
        "DocumentParseTool",
        "ContractClassifyTool",
        "ClauseExtractTool",
        "FieldExtractTool",
        "TemplateMatchTool",
    ],
    "ContractReviewSkill": [
        "RuleEngineTool",
        "LocalRagTool",
    ],
    "ReviewReportingSkill": [
        "BuildReportTool",
    ],
}


class ContractReviewAgent:
    prompt_version = "contract_review_agent_main@v0.3.0"

    def __init__(self, store: JsonStore) -> None:
        self.store = store

    def run(self, contract_id: str) -> None:
        try:
            contract = self.store.get_contract(contract_id)
            if not contract:
                return
            runtime = self._load_runtime_agent()
            self._validate_runtime_configuration(runtime)
            self._set_status(contract_id, "Understanding", "合同理解中")
            self.store.update_contract(contract_id, agent_runtime=runtime["public_config"])
            self._event(
                contract_id,
                "Observe",
                "agent_decision",
                f"发现合同入库事件，启动「{runtime['config']['name']}」。",
                extra={"agent_runtime": runtime["public_config"]},
            )
            for warning in runtime["warnings"]:
                self._event(contract_id, "Observe", "agent_warning", warning, visible=True)

            understanding_skill = ContractUnderstandingSkill(agent_config=runtime["config"])
            understanding_result = self._call_skill(
                contract_id,
                understanding_skill.name,
                lambda: understanding_skill.run(contract),
            )
            understanding = understanding_result["data"]
            text = understanding["text"]
            contract_type = understanding["contract_type"]
            clauses = understanding.get("clauses") or []
            fields = understanding["fields"]
            review_strategy = match_strategy(contract_type, understanding["template_match"])
            self.store.update_contract(
                contract_id,
                parsed_text=understanding["preview"],
                contract_type=contract_type,
                clauses=clauses,
                fields=fields,
                template_match=understanding["template_match"],
                review_strategy=review_strategy,
            )

            self._set_status(contract_id, "Reviewing", "规则审查与 RAG 检索中")
            self._event(
                contract_id,
                "Plan",
                "agent_decision",
                f"已完成合同理解，选用「{review_strategy['name']}」，按主智能体配置进入规则审查和证据检索。",
                visible=True,
                extra={"review_strategy": review_strategy},
            )
            review_skill = ContractReviewSkill(llm_client=runtime["llm_client"], agent_config=runtime["config"])
            review_result = self._call_skill(
                contract_id,
                review_skill.name,
                lambda: review_skill.run(text, contract_type, fields, clauses=clauses, strategy=review_strategy),
            )
            review_data = review_result["data"]
            risks = review_data["risks"]
            rule_events = review_data.get("rule_events") or []
            incomplete_rules = review_data.get("incomplete_rules") or [
                event for event in rule_events if not event.get("evaluated", True)
            ]
            executed_rules = int(review_data.get("executed_rules") or len(rule_events) or len(risks))
            passed_rules = sum(1 for event in rule_events if event.get("evaluated", True) and event.get("passed"))

            self._event(
                contract_id,
                "Verify",
                "agent_decision",
                f"规则审查完成，命中 {len(risks)} 条风险，{len(incomplete_rules)} 条规则未完成判断。",
                visible=True,
            )
            reporting_skill = ReviewReportingSkill(llm_client=runtime["llm_client"], agent_config=runtime["config"])
            report_result = self._call_skill(
                contract_id,
                reporting_skill.name,
                lambda: reporting_skill.run(
                    {
                        **contract,
                        "contract_type": contract_type,
                        "clauses": clauses,
                        "fields": fields,
                        "review_strategy": review_strategy,
                    },
                    risks,
                ),
            )

            report_data = {
                **report_result["data"],
                "executed_rules": executed_rules,
                "passed_rules": passed_rules,
                "rule_events": rule_events,
                "incomplete_rules": incomplete_rules,
                "incomplete_rule_count": len(incomplete_rules),
                "reviewed_rule_ids": [event.get("rule_id") for event in rule_events if event.get("rule_id")],
            }
            flow_decision = decide_contract_flow(
                {
                    **contract,
                    "contract_type": contract_type,
                    "clauses": clauses,
                    "fields": fields,
                    "review_strategy": review_strategy,
                },
                risks,
                report_data,
                review_strategy,
            )
            report_data["flow_decision"] = flow_decision
            next_status = flow_decision["status"]
            status_text = flow_decision["status_text"]
            self._event(
                contract_id,
                "Report",
                "agent_result",
                report_data["summary"],
                visible=True,
            )
            self._event(
                contract_id,
                "Flow",
                "flow_decision",
                f"{flow_decision['flow_strategy']['name']}：{flow_decision['reason']} {flow_decision['next_action']}",
                visible=True,
                extra={"flow_decision": flow_decision},
            )
            self.store.update_contract(
                contract_id,
                status=next_status,
                status_text=status_text,
                parsed_text=understanding["preview"],
                contract_type=contract_type,
                clauses=clauses,
                fields=fields,
                template_match=understanding["template_match"],
                review_strategy=review_strategy,
                flow_decision=flow_decision,
                agent_runtime=runtime["public_config"],
                risks=risks,
                report=report_data,
                agent_prompt_version=runtime["prompt_version"],
            )
        except Exception as exc:  # pragma: no cover
            self.store.update_contract(
                contract_id,
                status="Failed",
                status_text="审核失败",
                error=str(exc),
            )
            self._event(
                contract_id,
                "Fail",
                "agent_error",
                f"审核链路失败：{exc}",
                visible=True,
                extra={"traceback": traceback.format_exc()},
            )

    def _call_skill(self, contract_id: str, skill_name: str, runner) -> dict[str, Any]:
        self._event(contract_id, "Act", "skill_started", f"开始执行 {skill_name}。", visible=True)
        result = runner()
        self._event(
            contract_id,
            "Act",
            "skill_completed",
            f"{skill_name} 执行完成，状态：{result.get('status')}，置信度：{result.get('confidence')}。",
            visible=True,
            extra={
                "skill_name": skill_name,
                "skill_version": result.get("skill_version"),
                "confidence": result.get("confidence"),
                "confidence_detail": self._extract_confidence_detail(result),
                "warnings": result.get("warnings", []),
            },
        )
        return result

    def _extract_confidence_detail(self, result: dict[str, Any]) -> dict[str, Any] | None:
        data = result.get("data") or {}
        if data.get("confidence_detail"):
            return data["confidence_detail"]
        tool_runs = data.get("tool_runs") or []
        details = [
            tool_run.get("confidence_detail")
            for tool_run in tool_runs
            if isinstance(tool_run, dict) and tool_run.get("confidence_detail")
        ]
        if details:
            return {"tool_details": details}
        return None

    def _load_runtime_agent(self) -> dict[str, Any]:
        config = get_agent(MAIN_AGENT_ID)
        if not config:
            raise ValueError(f"未找到合同智审主智能体配置：{MAIN_AGENT_ID}")
        if not config.get("enabled", True):
            raise ValueError(f"合同智审主智能体已停用：{MAIN_AGENT_ID}")
        tools = set(config.get("tools") or [])
        model = config.get("model") or {}
        warnings = []
        if "LLMClient" in tools:
            llm_client = build_llm_client(model)
        else:
            llm_client = None
            if model.get("enabled"):
                warnings.append("主智能体已启用大模型配置，但未选择 LLMClient 工具，本次审核不会调用大模型。")
        public_config = self._public_agent_config(config, llm_client is not None)
        prompt_version = f"{config.get('id')}@{config.get('updated_at') or 'default'}"
        return {
            "config": config,
            "public_config": public_config,
            "llm_client": llm_client,
            "prompt_version": prompt_version,
            "warnings": warnings,
        }

    def _validate_runtime_configuration(self, runtime: dict[str, Any]) -> None:
        skills = set(runtime["config"].get("skills") or [])
        tools = set(runtime["config"].get("tools") or [])
        missing = [skill for skill in REQUIRED_REVIEW_SKILLS if skill not in skills]
        if missing:
            raise ValueError(f"主智能体缺少必需技能：{', '.join(missing)}")
        missing_tools = []
        for skill in REQUIRED_REVIEW_SKILLS:
            for tool in REQUIRED_TOOLS_BY_SKILL.get(skill, []):
                if tool not in tools:
                    missing_tools.append(f"{skill}.{tool}")
        if missing_tools:
            raise ValueError(f"主智能体缺少必需工具：{', '.join(missing_tools)}")

    def _public_agent_config(self, config: dict[str, Any], llm_configured: bool) -> dict[str, Any]:
        model = dict(config.get("model") or {})
        api_key = str(model.pop("api_key", "") or "")
        model["api_key_configured"] = bool(api_key)
        model["api_key_mask"] = f"{api_key[:4]}****{api_key[-4:]}" if len(api_key) > 8 else ("****" if api_key else "")
        model["runtime_configured"] = llm_configured
        return {
            "id": config.get("id"),
            "name": config.get("name"),
            "description": config.get("description"),
            "system_prompt": config.get("system_prompt"),
            "user_prompt": config.get("user_prompt"),
            "skills": config.get("skills") or [],
            "tools": config.get("tools") or [],
            "model": model,
            "enabled": config.get("enabled", True),
        }

    def _set_status(self, contract_id: str, status: str, status_text: str) -> None:
        self.store.update_contract(contract_id, status=status, status_text=status_text)

    def _event(
        self,
        contract_id: str,
        phase: str,
        event_type: str,
        message: str,
        visible: bool = True,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.store.append_event(
            contract_id,
            {
                "phase": phase,
                "event_type": event_type,
                "message": message,
                "visible_to_user": visible,
                **(extra or {}),
            },
        )
