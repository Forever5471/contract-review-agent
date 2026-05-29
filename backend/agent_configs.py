from __future__ import annotations

import json
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

from .storage import DATA_DIR, ROOT_DIR, now_iso


AGENTS_FILE = DATA_DIR / "agents.json"
_LOCK = threading.RLock()

SKILL_DIRS = {
    "ContractIntakeSkill": ROOT_DIR / "backend/agent_skills/contract_intake",
    "ContractUnderstandingSkill": ROOT_DIR / "backend/agent_skills/contract_understanding",
    "ContractReviewSkill": ROOT_DIR / "backend/agent_skills/contract_review",
    "ReviewReportingSkill": ROOT_DIR / "backend/agent_skills/review_reporting",
}

TOOL_FILES = {
    "DocumentParseTool": ROOT_DIR / "backend/tools/parse_document.py",
    "ContractClassifyTool": ROOT_DIR / "backend/tools/classify_contract.py",
    "ClauseExtractTool": ROOT_DIR / "backend/tools/extract_clauses.py",
    "FieldExtractTool": ROOT_DIR / "backend/tools/extract_fields.py",
    "TemplateMatchTool": ROOT_DIR / "backend/tools/match_template.py",
    "RuleEngineTool": ROOT_DIR / "backend/tools/execute_rules.py",
    "LocalRagTool": ROOT_DIR / "backend/tools/local_rag.py",
    "BuildReportTool": ROOT_DIR / "backend/tools/build_report.py",
    "LLMClient": ROOT_DIR / "backend/llm.py",
}

SKILL_CATALOG: list[dict[str, Any]] = [
    {
        "id": "ContractIntakeSkill",
        "name": "合同入库技能",
        "description": "接收上传文件，保存合同元数据，并初始化审核状态。",
        "inputs": ["file", "source", "business_dept", "initiator"],
        "outputs": ["contract"],
        "tools": ["JsonStore"],
    },
    {
        "id": "ContractUnderstandingSkill",
        "name": "合同理解技能",
        "description": "解析合同文本、识别合同类型、抽取条款对象和结构化字段并完成模板匹配。",
        "inputs": ["contract.file_path", "contract.file_name"],
        "outputs": ["text", "contract_type", "clauses", "fields", "template_match"],
        "tools": ["DocumentParseTool", "ContractClassifyTool", "ClauseExtractTool", "FieldExtractTool", "TemplateMatchTool"],
    },
    {
        "id": "ContractReviewSkill",
        "name": "合同规则审核技能",
        "description": "根据命中的审核策略执行关联规则，产出风险项和规则执行证据。",
        "inputs": ["text", "contract_type", "fields", "review_strategy"],
        "outputs": ["risks", "rule_events", "confidence_detail"],
        "tools": ["RuleEngineTool", "LocalRagTool"],
    },
    {
        "id": "ReviewReportingSkill",
        "name": "审核报告生成技能",
        "description": "汇总风险、角色意见和人工确认建议，生成最终审核报告。",
        "inputs": ["contract", "risks"],
        "outputs": ["report", "default_human_review_opinion"],
        "tools": ["BuildReportTool", "LLMClient"],
    },
]

TOOL_CATALOG: list[dict[str, Any]] = [
    {"id": "DocumentParseTool", "name": "文档解析工具", "description": "读取 TXT/MD/PDF/Word 文件并生成合同文本预览。", "used_by": ["ContractUnderstandingSkill"]},
    {"id": "ContractClassifyTool", "name": "合同分类工具", "description": "根据文件名和正文关键词识别合同类型。", "used_by": ["ContractUnderstandingSkill"]},
    {"id": "ClauseExtractTool", "name": "条款抽取工具", "description": "把合同正文拆分为条款对象，包含编号、标题、类型、原文和位置。", "used_by": ["ContractUnderstandingSkill", "ContractReviewSkill"]},
    {"id": "FieldExtractTool", "name": "字段抽取工具", "description": "抽取主体、金额、付款、发票、签章、生效、安全、违约等结构化字段。", "used_by": ["ContractUnderstandingSkill"]},
    {"id": "TemplateMatchTool", "name": "模板匹配工具", "description": "按合同类型检查标准章节覆盖情况，输出匹配度和缺失章节。", "used_by": ["ContractUnderstandingSkill"]},
    {"id": "RuleEngineTool", "name": "规则引擎工具", "description": "执行审核策略关联的脚本规则和指令规则。", "used_by": ["ContractReviewSkill"]},
    {"id": "LocalRagTool", "name": "本地知识检索工具", "description": "为规则审查提供制度、条款和审查依据检索结果。", "used_by": ["ContractReviewSkill"]},
    {"id": "BuildReportTool", "name": "审核报告工具", "description": "汇总风险、角色意见、结论和人工确认建议。", "used_by": ["ReviewReportingSkill"]},
    {"id": "LLMClient", "name": "大模型调用工具", "description": "调用已配置的大模型完成参数抽取、指令规则判断、摘要润色和意见草稿。", "used_by": ["ContractReviewSkill", "ReviewReportingSkill"]},
]


DEFAULT_AGENTS: list[dict[str, Any]] = [
    {
        "id": "contract-review-main",
        "name": "合同智审主智能体",
        "description": "编排合同理解、规则审查、报告生成和人工确认的主智能体。",
        "system_prompt": "你是企业合同智能审核助手，需基于合同文本、结构化字段、规则配置和证据输出审查结论。",
        "user_prompt": "请审查上传合同，识别合同类型、抽取关键字段、执行规则并生成审核报告。",
        "skills": [
            "ContractIntakeSkill",
            "ContractUnderstandingSkill",
            "ContractReviewSkill",
            "ReviewReportingSkill",
        ],
        "tools": [
            "DocumentParseTool",
            "ContractClassifyTool",
            "ClauseExtractTool",
            "FieldExtractTool",
            "TemplateMatchTool",
            "RuleEngineTool",
            "LocalRagTool",
            "BuildReportTool",
            "LLMClient",
        ],
        "model": {
            "provider": "glm",
            "model": "glm-5",
            "base_url": "https://api.z.ai/api/paas/v4",
            "temperature": 0.2,
            "api_key": "",
            "enabled": False,
        },
        "enabled": True,
    }
]


def list_agents() -> list[dict[str, Any]]:
    return _load_agents()


def list_public_agents() -> list[dict[str, Any]]:
    return [_public_agent(agent) for agent in _load_agents()]


def list_skill_catalog() -> list[dict[str, Any]]:
    return [_with_skill_files(skill) for skill in deepcopy(SKILL_CATALOG)]


def list_tool_catalog() -> list[dict[str, Any]]:
    return [_with_tool_files(tool) for tool in deepcopy(TOOL_CATALOG)]


def get_agent(agent_id: str) -> dict[str, Any] | None:
    for agent in _load_agents():
        if agent["id"] == agent_id:
            return agent
    return None


def save_agent(payload: dict[str, Any], original_id: str | None = None) -> dict[str, Any]:
    agent = normalize_agent(payload)
    with _LOCK:
        agents = _load_agents()
        lookup_id = original_id or agent["id"]
        for existing in agents:
            if existing["id"] == agent["id"] and existing["id"] != lookup_id:
                raise ValueError(f"智能体编号 {agent['id']} 已存在")
        for index, existing in enumerate(agents):
            if existing["id"] == lookup_id:
                if not agent["model"].get("api_key") and existing.get("model", {}).get("api_key"):
                    agent["model"]["api_key"] = existing["model"]["api_key"]
                agent["created_at"] = existing.get("created_at") or now_iso()
                agent["updated_at"] = now_iso()
                agents[index] = agent
                _write_agents(agents)
                return agent
        agent["created_at"] = now_iso()
        agent["updated_at"] = now_iso()
        agents.append(agent)
        _write_agents(agents)
        return agent


def delete_agent(agent_id: str) -> None:
    with _LOCK:
        agents = _load_agents()
        next_agents = [agent for agent in agents if agent["id"] != agent_id]
        if len(next_agents) == len(agents):
            raise KeyError(agent_id)
        _write_agents(next_agents)


def reset_agents() -> list[dict[str, Any]]:
    agents = [normalize_agent(agent) for agent in deepcopy(DEFAULT_AGENTS)]
    now = now_iso()
    for agent in agents:
        agent["created_at"] = now
        agent["updated_at"] = now
    _write_agents(agents)
    return agents


def normalize_agent(payload: dict[str, Any]) -> dict[str, Any]:
    agent_id = str(payload.get("id") or "").strip()
    name = str(payload.get("name") or "").strip()
    if not agent_id:
        raise ValueError("智能体编号不能为空")
    if not name:
        raise ValueError("智能体名称不能为空")
    model = payload.get("model") if isinstance(payload.get("model"), dict) else {}
    return {
        "id": agent_id,
        "name": name,
        "description": str(payload.get("description") or "").strip(),
        "system_prompt": str(payload.get("system_prompt") or "").strip(),
        "user_prompt": str(payload.get("user_prompt") or "").strip(),
        "skills": _normalize_list(payload.get("skills")),
        "tools": _normalize_list(payload.get("tools")),
        "model": {
            "provider": str(model.get("provider") or "openai-compatible").strip(),
            "model": str(model.get("model") or "").strip(),
            "base_url": str(model.get("base_url") or "").strip(),
            "temperature": _to_float(model.get("temperature"), 0.2),
            "api_key": str(model.get("api_key") or "").strip(),
            "enabled": bool(model.get("enabled", False)),
        },
        "enabled": bool(payload.get("enabled", True)),
        "created_at": payload.get("created_at") or "",
        "updated_at": payload.get("updated_at") or "",
    }


def _normalize_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [item.strip() for item in value.replace("，", ",").split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _to_float(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _public_agent(agent: dict[str, Any]) -> dict[str, Any]:
    item = deepcopy(agent)
    model = item.get("model") if isinstance(item.get("model"), dict) else {}
    api_key = str(model.get("api_key") or "")
    model.pop("api_key", None)
    model["api_key_configured"] = bool(api_key)
    model["api_key_mask"] = _mask_secret(api_key)
    item["model"] = model
    return item


def _mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}****{value[-4:]}"


def _with_skill_files(skill: dict[str, Any]) -> dict[str, Any]:
    root = SKILL_DIRS.get(skill["id"])
    if not root:
        return skill
    return {
        **skill,
        "package_path": _relative_path(root),
        "file_tree": _resource_tree(root),
        "readme": _safe_read(root / "SKILL.md"),
    }


def _with_tool_files(tool: dict[str, Any]) -> dict[str, Any]:
    path = TOOL_FILES.get(tool["id"])
    if not path:
        return tool
    return {
        **tool,
        "package_path": _relative_path(path.parent),
        "file_tree": _resource_tree(path),
        "source": _safe_read(path),
    }


def _resource_tree(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if path.is_file():
        return {
            "name": path.name,
            "type": "file",
            "path": _relative_path(path),
            "content": _safe_read(path),
        }
    children = []
    preferred_order = {"SKILL.md": 0, "scripts": 1, "references": 2, "skill.py": 3, "__init__.py": 4}
    for child in sorted(path.iterdir(), key=lambda item: (preferred_order.get(item.name, 20), item.name.lower())):
        if child.name in {"__pycache__", ".DS_Store", ".gitkeep"}:
            continue
        if child.name.endswith(".pyc"):
            continue
        node = _resource_tree(child)
        if node:
            children.append(node)
    return {
        "name": path.name,
        "type": "dir",
        "path": _relative_path(path),
        "children": children,
    }


def _safe_read(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")[:12000]
    except UnicodeDecodeError:
        return ""


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def _load_agents() -> list[dict[str, Any]]:
    with _LOCK:
        if not AGENTS_FILE.exists():
            return [normalize_agent(agent) for agent in deepcopy(DEFAULT_AGENTS)]
        data = json.loads(AGENTS_FILE.read_text(encoding="utf-8"))
        raw_agents = data.get("agents", data if isinstance(data, list) else [])
        return [normalize_agent(agent) for agent in raw_agents]


def _write_agents(agents: list[dict[str, Any]]) -> None:
    with _LOCK:
        AGENTS_FILE.write_text(
            json.dumps({"agents": agents}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
