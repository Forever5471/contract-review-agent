from __future__ import annotations

from typing import Any

from ...tools.classify_contract import ContractClassifyTool
from ...tools.extract_clauses import ClauseExtractTool
from ...tools.extract_fields import FieldExtractTool
from ...tools.match_template import TemplateMatchTool
from ...tools.parse_document import DocumentParseTool


class ContractUnderstandingSkill:
    name = "ContractUnderstandingSkill"
    version = "0.2.0"

    def __init__(self, agent_config: dict[str, Any] | None = None) -> None:
        self.agent_config = agent_config or {}
        self.parse_tool = DocumentParseTool()
        self.classify_tool = ContractClassifyTool()
        self.clause_tool = ClauseExtractTool()
        self.extract_tool = FieldExtractTool()
        self.template_tool = TemplateMatchTool()

    def run(self, contract: dict[str, Any]) -> dict[str, Any]:
        parse_result = self.parse_tool.run(contract["file_path"])
        text = parse_result["data"]["text"]
        classify_result = self.classify_tool.run(text, contract["file_name"])
        clause_result = self.clause_tool.run(text, contract.get("id", ""))
        extract_result = self.extract_tool.run(text)
        contract_type = classify_result["data"]["contract_type"]
        template_result = self.template_tool.run(contract_type, text)

        tool_runs = [
            self._tool_summary(parse_result),
            self._tool_summary(classify_result),
            self._tool_summary(clause_result),
            self._tool_summary(extract_result),
            self._tool_summary(template_result),
        ]
        warnings = [
            warning
            for result in [parse_result, classify_result, clause_result, extract_result, template_result]
            for warning in result.get("warnings", [])
        ]
        confidence = round(
            min(
                result.get("confidence", 0)
                for result in [parse_result, classify_result, clause_result, extract_result, template_result]
            ),
            2,
        )
        confidence_detail = self._calculate_confidence_detail(
            parse_result,
            classify_result,
            clause_result,
            extract_result,
            template_result,
            confidence,
        )
        return {
            "skill_name": self.name,
            "skill_version": self.version,
            "status": "success" if text else "warning",
            "confidence": confidence,
            "data": {
                "text": text,
                "preview": parse_result["data"]["preview"],
                "chunks": parse_result["data"]["chunks"],
                "contract_type": contract_type,
                "classification": classify_result["data"],
                "clauses": clause_result["data"]["clauses"],
                "fields": extract_result["data"],
                "template_match": template_result["data"],
                "confidence_detail": confidence_detail,
                "tool_runs": tool_runs,
            },
            "evidence": (
                parse_result.get("evidence", [])
                + classify_result.get("evidence", [])
                + clause_result.get("evidence", [])
                + extract_result.get("evidence", [])
                + template_result.get("evidence", [])
            )[:20],
            "warnings": warnings,
        }

    def _tool_summary(self, result: dict[str, Any]) -> dict[str, Any]:
        return {
            "tool_name": result.get("tool_name"),
            "tool_version": result.get("tool_version"),
            "status": result.get("status"),
            "confidence": result.get("confidence"),
            "confidence_detail": (result.get("data") or {}).get("confidence_detail"),
            "warnings": result.get("warnings", []),
        }

    def _calculate_confidence_detail(
        self,
        parse_result: dict[str, Any],
        classify_result: dict[str, Any],
        clause_result: dict[str, Any],
        extract_result: dict[str, Any],
        template_result: dict[str, Any],
        overall: float,
    ) -> dict[str, Any]:
        return {
            "overall": overall,
            "document_parse": parse_result.get("confidence"),
            "contract_classify": classify_result.get("confidence"),
            "clause_extract": clause_result.get("confidence"),
            "field_extract": extract_result.get("confidence"),
            "template_match": template_result.get("confidence"),
            "method": "minimum_tool_confidence",
        }
