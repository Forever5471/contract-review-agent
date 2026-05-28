from __future__ import annotations

from typing import Any

from ...llm import build_llm_client
from ...tools.execute_rules import RuleEngineTool
from ...tools.local_rag import LocalRagTool


class ContractReviewSkill:
    name = "ContractReviewSkill"
    version = "0.3.0"

    def __init__(self, llm_client: Any | None = None, agent_config: dict[str, Any] | None = None) -> None:
        self.rag_tool = LocalRagTool()
        self.agent_config = agent_config or {}
        llm_tool_enabled = not self.agent_config or "LLMClient" in set(self.agent_config.get("tools") or [])
        self.llm_client = llm_client if llm_client is not None else (
            build_llm_client(self.agent_config.get("model")) if llm_tool_enabled else None
        )
        self.rule_engine = RuleEngineTool(self.rag_tool, llm=self.llm_client, agent_config=self.agent_config)

    def run(
        self,
        text: str,
        contract_type: str,
        fields: dict[str, Any],
        clauses: list[dict[str, Any]] | None = None,
        strategy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        rule_result = self.rule_engine.run(text, contract_type, fields, clauses=clauses, strategy=strategy)
        return {
            "skill_name": self.name,
            "skill_version": self.version,
            "status": rule_result["status"],
            "confidence": rule_result["confidence"],
            "data": {
                **rule_result["data"],
                "tool_runs": [
                    {
                        "tool_name": rule_result.get("tool_name"),
                        "tool_version": rule_result.get("tool_version"),
                        "status": rule_result.get("status"),
                        "confidence": rule_result.get("confidence"),
                        "confidence_detail": rule_result["data"].get("confidence_detail"),
                        "llm_enabled": rule_result["data"].get("llm_enabled"),
                        "llm_provider": rule_result["data"].get("llm_provider"),
                        "llm_model": rule_result["data"].get("llm_model"),
                        "warnings": rule_result.get("warnings", []),
                    }
                ],
            },
            "evidence": rule_result.get("evidence", []),
            "warnings": rule_result.get("warnings", []),
        }
