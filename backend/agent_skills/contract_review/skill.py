from __future__ import annotations

from typing import Any

from ...llm import build_llm_client
from ...tools.execute_rules import RuleEngineTool
from ...tools.local_rag import LocalRagTool


class ContractReviewSkill:
    name = "ContractReviewSkill"
    version = "0.3.0"

    def __init__(self) -> None:
        self.rag_tool = LocalRagTool()
        self.llm_client = build_llm_client()
        self.rule_engine = RuleEngineTool(self.rag_tool, llm=self.llm_client)

    def run(self, text: str, contract_type: str, fields: dict[str, Any]) -> dict[str, Any]:
        rule_result = self.rule_engine.run(text, contract_type, fields)
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
