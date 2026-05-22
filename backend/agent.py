from __future__ import annotations

import traceback
from typing import Any

from .agent_skills.contract_review import ContractReviewSkill
from .agent_skills.contract_understanding import ContractUnderstandingSkill
from .agent_skills.review_reporting import ReviewReportingSkill
from .storage import JsonStore


class ContractReviewAgent:
    prompt_version = "contract_review_agent_main@v0.2.0"

    def __init__(self, store: JsonStore) -> None:
        self.store = store
        self.understanding_skill = ContractUnderstandingSkill()
        self.review_skill = ContractReviewSkill()
        self.reporting_skill = ReviewReportingSkill()

    def run(self, contract_id: str) -> None:
        try:
            contract = self.store.get_contract(contract_id)
            if not contract:
                return
            self._set_status(contract_id, "Understanding", "合同理解中")
            self._event(contract_id, "Observe", "agent_decision", "发现合同入库事件，准备执行合同审核。")

            understanding_result = self._call_skill(
                contract_id,
                self.understanding_skill.name,
                lambda: self.understanding_skill.run(contract),
            )
            understanding = understanding_result["data"]
            text = understanding["text"]
            contract_type = understanding["contract_type"]
            fields = understanding["fields"]

            self._set_status(contract_id, "Reviewing", "规则审查与 RAG 检索中")
            self._event(
                contract_id,
                "Plan",
                "agent_decision",
                "已完成合同理解，进入规则审查和证据检索。",
                visible=True,
            )
            review_result = self._call_skill(
                contract_id,
                self.review_skill.name,
                lambda: self.review_skill.run(text, contract_type, fields),
            )
            risks = review_result["data"]["risks"]

            self._event(
                contract_id,
                "Verify",
                "agent_decision",
                f"规则审查完成，命中 {len(risks)} 条风险。",
                visible=True,
            )
            report_result = self._call_skill(
                contract_id,
                self.reporting_skill.name,
                lambda: self.reporting_skill.run({**contract, "contract_type": contract_type, "fields": fields}, risks),
            )

            next_status = "NeedHumanConfirm" if report_result["data"]["need_human_confirm"] else "Completed"
            status_text = "待人工确认" if next_status == "NeedHumanConfirm" else "审核完成"
            self.store.update_contract(
                contract_id,
                status=next_status,
                status_text=status_text,
                parsed_text=understanding["preview"],
                contract_type=contract_type,
                fields=fields,
                template_match=understanding["template_match"],
                risks=risks,
                report=report_result["data"],
                agent_prompt_version=self.prompt_version,
            )
            self._event(
                contract_id,
                "Report",
                "agent_result",
                report_result["data"]["summary"],
                visible=True,
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
