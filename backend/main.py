from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, List, Optional, Union
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .agent import ContractReviewAgent
from .agent_configs import (
    delete_agent,
    get_agent,
    list_agents,
    list_public_agents,
    list_skill_catalog,
    list_tool_catalog,
    reset_agents,
    save_agent,
)
from .agent_skills.contract_intake import ContractIntakeSkill
from .agent_skills.contract_understanding import ContractUnderstandingSkill
from .flow_strategies import (
    delete_flow_strategy,
    get_flow_strategy,
    list_flow_strategies,
    reset_flow_strategies,
    save_flow_strategy,
)
from .llm import build_llm_client, get_llm_status
from .rules import delete_rule, get_rule, list_rules, normalize_rule, reset_rules, save_rule
from .storage import JsonStore, ROOT_DIR, UPLOAD_DIR, WORKSPACE_DIR, now_iso
from .strategies import (
    delete_strategy,
    get_strategy,
    list_strategies,
    match_strategy,
    reset_strategies,
    save_strategy,
)
from .tools.execute_rules import RuleEngineTool
from .tools.local_rag import LocalRagTool


app = FastAPI(title="Contract Review Agent MVP")
store = JsonStore()
intake_skill = ContractIntakeSkill()
understanding_skill = ContractUnderstandingSkill()
knowledge_tool = LocalRagTool()
agent = ContractReviewAgent(store)
KNOWLEDGE_FILE_SUFFIXES = {".docx", ".doc", ".pdf", ".md", ".txt"}


class HumanReviewRequest(BaseModel):
    action: str
    opinion: str = ""
    reviewer: str = ""


class RuleRequest(BaseModel):
    id: str
    name: str
    mode: str = "脚本模式"
    priority: str = "P2"
    risk_level: str = ""
    scope: Union[List[str], str] = []
    description: str = ""
    enabled: bool = True
    script: str = ""
    instruction: str = ""
    input_params: List[dict] = []
    output_params: List[dict] = []


class AgentConfigRequest(BaseModel):
    id: str
    name: str
    description: str = ""
    system_prompt: str = ""
    user_prompt: str = ""
    skills: Union[List[str], str] = []
    tools: Union[List[str], str] = []
    model: dict = {}
    enabled: bool = True


class StrategyRequest(BaseModel):
    id: str
    name: str
    template_type: str
    description: str = ""
    rule_ids: Union[List[str], str] = []
    agent_instruction: str = ""
    enabled: bool = True


class FlowStrategyRequest(BaseModel):
    id: str
    name: str
    description: str = ""
    review_strategy_ids: Union[List[str], str] = []
    auto_pass_max_p0: int = 0
    auto_pass_max_p1: int = 0
    auto_pass_max_general: int = 2
    auto_pass_max_amount: float = 100000
    human_confirm_min_amount: float = 100000
    human_confirm_min_p1: int = 1
    human_confirm_min_general: int = 3
    need_revision_min_p0: int = 1
    blocked_rule_ids: Union[List[str], str] = []
    need_revision_rule_ids: Union[List[str], str] = []
    enabled: bool = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/llm/status")
def llm_status() -> dict:
    runtime_agent = get_agent("contract-review-main")
    model = (runtime_agent or {}).get("model") or {}
    tools = set((runtime_agent or {}).get("tools") or [])
    configured = bool(
        "LLMClient" in tools
        and model.get("enabled")
        and model.get("api_key")
        and model.get("provider")
        and model.get("model")
        and (model.get("base_url") or model.get("provider") == "glm")
    )
    if configured:
        return {
            "configured": True,
            "provider": model.get("provider"),
            "model": model.get("model"),
            "base_url": model.get("base_url"),
            "api_key_set": True,
            "source": "agent_config",
        }
    if model.get("enabled") and "LLMClient" not in tools:
        return {
            "configured": False,
            "provider": model.get("provider"),
            "model": model.get("model"),
            "api_key_set": bool(model.get("api_key")),
            "source": "agent_config",
            "warning": "主智能体未选择 LLMClient 工具。",
        }
    return {**get_llm_status(), "source": "env"}


@app.get("/api/rules/stats")
def rule_stats() -> dict:
    rules = list_rules()
    high_priorities = {"P0", "P1"}
    general_priorities = {"P2", "P3"}
    enabled_rules = [rule for rule in rules if rule.get("enabled", True)]
    high_rules = [rule for rule in enabled_rules if rule.get("priority") in high_priorities]
    general_rules = [rule for rule in enabled_rules if rule.get("priority") in general_priorities]
    return {
        "high_risk_rules": len(high_rules),
        "general_risk_rules": len(general_rules),
        "total_rules": len(enabled_rules),
        "configured_rules": len(rules),
        "disabled_rules": len(rules) - len(enabled_rules),
        "priority_counts": {
            priority: sum(1 for rule in enabled_rules if rule.get("priority") == priority)
            for priority in ["P0", "P1", "P2", "P3"]
        },
    }


@app.get("/api/rules")
def rules_list() -> dict:
    return {"items": list_rules()}


@app.get("/api/rules/{rule_id}")
def rule_detail(rule_id: str) -> dict:
    rule = get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"item": rule}


@app.post("/api/rules")
def rule_create(payload: RuleRequest) -> dict:
    try:
        rule = save_rule(_model_to_dict(payload))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": rule}


@app.put("/api/rules/{rule_id}")
def rule_update(rule_id: str, payload: RuleRequest) -> dict:
    if not get_rule(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")
    try:
        rule = save_rule(_model_to_dict(payload), original_id=rule_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": rule}


@app.delete("/api/rules/{rule_id}")
def rule_delete(rule_id: str) -> dict:
    try:
        delete_rule(rule_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Rule not found") from exc
    return {"ok": True}


@app.post("/api/rules/reset")
def rule_reset() -> dict:
    return {"items": reset_rules()}


@app.get("/api/knowledge")
def knowledge_list(refresh: bool = False) -> dict:
    return knowledge_tool.list_entries(refresh=refresh)


@app.get("/api/knowledge/search")
def knowledge_search(q: str = "", top_k: int = 8) -> dict:
    query = q.strip()
    if not query:
        return {**knowledge_tool.list_entries(), "query": ""}
    limit = max(1, min(top_k, 20))
    result = knowledge_tool.run(query, top_k=limit)
    return {
        "tool_name": result["tool_name"],
        "tool_version": result["tool_version"],
        "query": query,
        "items": result["data"]["results"],
        "confidence": result["confidence"],
        "confidence_detail": result["data"]["confidence_detail"],
        "warnings": result.get("warnings", []),
    }


@app.post("/api/knowledge/upload")
def knowledge_upload(category: str = Form(...), file: UploadFile = File(...)) -> dict:
    category_name = category.strip()
    if category_name not in knowledge_tool.categories():
        raise HTTPException(status_code=400, detail="不支持的知识分类")
    original_name = Path(file.filename or "").name.strip()
    suffix = Path(original_name).suffix.lower()
    if suffix not in KNOWLEDGE_FILE_SUFFIXES:
        raise HTTPException(status_code=400, detail="仅支持 Word、PDF、TXT、MD 文件")
    safe_name = _safe_filename(original_name) or f"knowledge-{uuid4().hex}{suffix}"
    target_dir = WORKSPACE_DIR / category_name
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / safe_name
    if target_path.exists():
        target_path = target_dir / f"{target_path.stem}-{uuid4().hex[:8]}{target_path.suffix}"
    with target_path.open("wb") as target:
        shutil.copyfileobj(file.file, target)
    knowledge = knowledge_tool.list_entries(refresh=True)
    return {
        "ok": True,
        "item": {
            "category": category_name,
            "source": str(target_path.relative_to(WORKSPACE_DIR)),
            "title": target_path.name,
        },
        "knowledge": knowledge,
    }


@app.get("/api/human-feedback")
def human_feedback_list() -> dict:
    items = _build_human_feedback_items(store.list_contracts())
    reject_count = sum(1 for item in items if item.get("action") == "reject")
    approve_count = sum(1 for item in items if item.get("action") == "approve")
    with_opinion_count = sum(1 for item in items if item.get("opinion"))
    rule_counts: dict[str, dict[str, Any]] = {}
    for item in items:
        for risk in item.get("risks", []):
            rule_id = str(risk.get("rule_id") or "").strip()
            if not rule_id:
                continue
            rule_counts.setdefault(
                rule_id,
                {"rule_id": rule_id, "rule_name": risk.get("rule_name") or rule_id, "count": 0},
            )
            rule_counts[rule_id]["count"] += 1
    top_rules = sorted(rule_counts.values(), key=lambda entry: entry["count"], reverse=True)[:8]
    return {
        "items": items,
        "summary": {
            "total": len(items),
            "approve_count": approve_count,
            "reject_count": reject_count,
            "with_opinion_count": with_opinion_count,
            "contract_count": len({item.get("contract_id") for item in items}),
            "top_rules": top_rules,
        },
    }


@app.post("/api/rules/debug")
def rule_debug(rule_json: str = Form(...), file: UploadFile = File(...)) -> dict:
    try:
        rule = normalize_rule(json.loads(rule_json))
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"规则配置无效：{exc}") from exc

    suffix = ""
    if file.filename and "." in file.filename:
        suffix = "." + file.filename.rsplit(".", 1)[-1]
    temp_path = UPLOAD_DIR / f"debug-rule-{uuid4().hex}{suffix}"
    try:
        with temp_path.open("wb") as target:
            shutil.copyfileobj(file.file, target)
        understanding = understanding_skill.run(
            {
                "file_path": str(temp_path),
                "file_name": file.filename or temp_path.name,
            }
        )["data"]
        runtime_agent = get_agent("contract-review-main") or {}
        tools = set(runtime_agent.get("tools") or [])
        llm_client = build_llm_client(runtime_agent.get("model")) if "LLMClient" in tools else None
        debug_rule_engine = RuleEngineTool(LocalRagTool(), llm=llm_client, agent_config=runtime_agent)
        result = debug_rule_engine.run_one(
            rule,
            understanding["text"],
            understanding["contract_type"],
            understanding["fields"],
            understanding.get("clauses") or [],
        )
    finally:
        temp_path.unlink(missing_ok=True)

    return {
        "ok": True,
        "understanding": {
            "contract_type": understanding["contract_type"],
            "fields": understanding["fields"],
            "clauses": understanding.get("clauses") or [],
            "preview": understanding["preview"],
            "confidence_detail": understanding.get("confidence_detail"),
        },
        "result": result,
    }


@app.get("/api/strategies")
def strategies_list() -> dict:
    return {"items": list_strategies(), "rules": list_rules()}


@app.get("/api/strategies/match")
def strategy_match(contract_type: str = "", template_name: str = "") -> dict:
    return {"item": match_strategy(contract_type, {"template_name": template_name})}


@app.post("/api/strategies")
def strategy_create(payload: StrategyRequest) -> dict:
    try:
        item = save_strategy(_model_to_dict(payload))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": item}


@app.put("/api/strategies/{strategy_id}")
def strategy_update(strategy_id: str, payload: StrategyRequest) -> dict:
    if not get_strategy(strategy_id):
        raise HTTPException(status_code=404, detail="Strategy not found")
    try:
        item = save_strategy(_model_to_dict(payload), original_id=strategy_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": item}


@app.delete("/api/strategies/{strategy_id}")
def strategy_delete(strategy_id: str) -> dict:
    try:
        delete_strategy(strategy_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Strategy not found") from exc
    return {"ok": True}


@app.post("/api/strategies/reset")
def strategies_reset() -> dict:
    return {"items": reset_strategies(), "rules": list_rules()}


@app.get("/api/flow-strategies")
def flow_strategies_list() -> dict:
    return {
        "items": list_flow_strategies(),
        "review_strategies": list_strategies(),
        "rules": list_rules(),
    }


@app.post("/api/flow-strategies")
def flow_strategy_create(payload: FlowStrategyRequest) -> dict:
    try:
        item = save_flow_strategy(_model_to_dict(payload))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": item}


@app.put("/api/flow-strategies/{flow_strategy_id}")
def flow_strategy_update(flow_strategy_id: str, payload: FlowStrategyRequest) -> dict:
    if not get_flow_strategy(flow_strategy_id):
        raise HTTPException(status_code=404, detail="Flow strategy not found")
    try:
        item = save_flow_strategy(_model_to_dict(payload), original_id=flow_strategy_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": item}


@app.delete("/api/flow-strategies/{flow_strategy_id}")
def flow_strategy_delete(flow_strategy_id: str) -> dict:
    try:
        delete_flow_strategy(flow_strategy_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Flow strategy not found") from exc
    return {"ok": True}


@app.post("/api/flow-strategies/reset")
def flow_strategies_reset() -> dict:
    return {
        "items": reset_flow_strategies(),
        "review_strategies": list_strategies(),
        "rules": list_rules(),
    }


@app.get("/api/agents")
def agents_list() -> dict:
    return {
        "items": list_public_agents(),
        "available_skills": list_skill_catalog(),
        "available_tools": list_tool_catalog(),
    }


@app.post("/api/agents")
def agent_create(payload: AgentConfigRequest) -> dict:
    try:
        item = save_agent(_model_to_dict(payload))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": _public_agent_response(item)}


@app.put("/api/agents/{agent_id}")
def agent_update(agent_id: str, payload: AgentConfigRequest) -> dict:
    if not get_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    try:
        item = save_agent(_model_to_dict(payload), original_id=agent_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": _public_agent_response(item)}


@app.delete("/api/agents/{agent_id}")
def agent_delete(agent_id: str) -> dict:
    try:
        delete_agent(agent_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Agent not found") from exc
    return {"ok": True}


@app.post("/api/agents/reset")
def agents_reset() -> dict:
    reset_agents()
    return {
        "items": list_public_agents(),
        "available_skills": list_skill_catalog(),
        "available_tools": list_tool_catalog(),
    }


@app.get("/api/contracts")
def list_contracts() -> dict:
    return {"items": [_summarize(item) for item in store.list_contracts()]}


@app.post("/api/contracts")
def create_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source: str = Form("upload"),
    business_dept: str = Form(""),
    initiator: str = Form(""),
) -> dict:
    file_hash, file_size = _hash_upload_file(file.file)
    existing = _find_contract_by_file_hash(file_hash)
    if existing:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "duplicate_contract",
                "message": f"该合同已存在：{existing.get('name') or existing.get('file_name') or existing['id']}，无需重复上传。",
                "existing_id": existing["id"],
                "existing_name": existing.get("name", ""),
            },
        )
    intake_result = intake_skill.run_upload(
        file.file,
        file.filename or "contract",
        source,
        business_dept,
        initiator,
        store,
    )
    contract = intake_result["data"]["contract"]
    contract["file_sha256"] = file_hash
    contract["file_size"] = file_size
    store.upsert_contract(contract)
    background_tasks.add_task(agent.run, contract["id"])
    return {"item": _summarize(contract)}


@app.get("/api/contracts/{contract_id}")
def get_contract(contract_id: str) -> dict:
    contract = store.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return {"item": contract}


@app.post("/api/contracts/{contract_id}/review")
def rerun_review(contract_id: str, background_tasks: BackgroundTasks) -> dict:
    contract = store.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    store.update_contract(
        contract_id,
        status="Pending",
        status_text="等待重新审核",
        risks=[],
        report=None,
        human_review=None,
        review={"events": []},
    )
    background_tasks.add_task(agent.run, contract_id)
    return {"ok": True}


@app.post("/api/contracts/{contract_id}/human-review")
def human_review(contract_id: str, payload: HumanReviewRequest) -> dict:
    contract = store.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    action = payload.action.strip().lower()
    if action not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="Unsupported human review action")

    if action == "approve":
        status = "Completed"
        status_text = "人工已确认：通过"
        decision = "确认通过"
        event_message = "人工审核已确认通过，合同可进入后续流转。"
    else:
        status = "NeedRevision"
        status_text = "人工已确认：不通过"
        decision = "确认不通过"
        event_message = "人工审核已确认不通过，需经办人补充或修订后重新提交。"

    human_review_data = {
        "action": action,
        "decision": decision,
        "opinion": payload.opinion.strip(),
        "reviewer": payload.reviewer.strip() or "人工审核人",
        "time": now_iso(),
    }
    updated = store.update_contract(
        contract_id,
        status=status,
        status_text=status_text,
        human_review=human_review_data,
    )
    store.append_event(
        contract_id,
        {
            "phase": "HumanConfirm",
            "event_type": "human_review",
            "message": event_message if not human_review_data["opinion"] else f"{event_message} 意见：{human_review_data['opinion']}",
            "visible_to_user": True,
            "human_review": human_review_data,
        },
    )
    return {"ok": True, "item": _summarize(updated)}


def _build_human_feedback_items(contracts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for contract in contracts:
        events = ((contract.get("review") or {}).get("events") or [])
        for index, event in enumerate(events):
            feedback = event.get("human_review")
            if event.get("event_type") != "human_review" or not isinstance(feedback, dict):
                continue
            key = _human_feedback_key(contract, feedback, event.get("time"))
            seen.add(key)
            items.append(_build_human_feedback_item(contract, feedback, event.get("time"), index))

        latest_feedback = contract.get("human_review")
        if isinstance(latest_feedback, dict):
            event_time = latest_feedback.get("time") or contract.get("updated_at") or contract.get("created_at")
            key = _human_feedback_key(contract, latest_feedback, event_time)
            if key not in seen:
                items.append(_build_human_feedback_item(contract, latest_feedback, event_time, len(events)))

    return sorted(items, key=lambda item: item.get("time") or "", reverse=True)


def _human_feedback_key(
    contract: dict[str, Any],
    feedback: dict[str, Any],
    event_time: Optional[str],
) -> tuple[str, str, str, str]:
    return (
        str(contract.get("id") or ""),
        str(event_time or feedback.get("time") or ""),
        str(feedback.get("action") or ""),
        str(feedback.get("opinion") or ""),
    )


def _build_human_feedback_item(
    contract: dict[str, Any],
    feedback: dict[str, Any],
    event_time: Optional[str],
    index: int,
) -> dict[str, Any]:
    fields = contract.get("fields") or {}
    risks = [_human_feedback_risk(risk) for risk in contract.get("risks") or []]
    report = contract.get("report") or {}
    rule_events = report.get("rule_events") or []
    passed_rules = [
        {
            "rule_id": event.get("rule_id"),
            "rule_name": event.get("rule_name"),
            "mode": event.get("mode"),
            "priority": event.get("priority"),
            "risk_level": event.get("risk_level"),
        }
        for event in rule_events
        if event.get("passed")
    ]
    matched_clauses = _unique_feedback_clauses(risks)
    review_strategy = contract.get("review_strategy") or {}
    flow_decision = contract.get("flow_decision") or {}
    time = str(event_time or feedback.get("time") or contract.get("updated_at") or "")
    return {
        "id": f"{contract.get('id', 'contract')}-feedback-{index}",
        "contract_id": contract.get("id"),
        "contract_name": contract.get("name"),
        "contract_type": contract.get("contract_type"),
        "status": contract.get("status"),
        "status_text": contract.get("status_text"),
        "created_at": contract.get("created_at"),
        "updated_at": contract.get("updated_at"),
        "business_dept": contract.get("business_dept"),
        "initiator": contract.get("initiator"),
        "source": contract.get("source"),
        "max_amount": fields.get("max_amount"),
        "action": feedback.get("action"),
        "decision": feedback.get("decision"),
        "opinion": str(feedback.get("opinion") or "").strip(),
        "reviewer": feedback.get("reviewer") or "人工审核人",
        "time": time,
        "review_strategy": {
            "id": review_strategy.get("id"),
            "name": review_strategy.get("name"),
            "template_type": review_strategy.get("template_type"),
        },
        "flow_decision": {
            "decision": flow_decision.get("decision"),
            "status": flow_decision.get("status"),
            "status_text": flow_decision.get("status_text"),
            "reason": flow_decision.get("reason"),
            "flow_strategy": (flow_decision.get("flow_strategy") or {}).get("name"),
        },
        "risk_summary": {
            "total": len(risks),
            "p0": sum(1 for risk in risks if risk.get("priority") == "P0"),
            "p1": sum(1 for risk in risks if risk.get("priority") == "P1"),
            "general": sum(1 for risk in risks if risk.get("priority") in {"P2", "P3"}),
        },
        "risks": risks,
        "passed_rules": passed_rules,
        "matched_clauses": matched_clauses,
        "default_opinion": report.get("default_human_review_opinion"),
        "report_summary": report.get("summary"),
        "report_conclusion": report.get("conclusion"),
    }


def _human_feedback_risk(risk: dict[str, Any]) -> dict[str, Any]:
    return {
        "rule_id": risk.get("rule_id"),
        "rule_name": risk.get("rule_name"),
        "mode": risk.get("mode"),
        "priority": risk.get("priority"),
        "risk_level": risk.get("risk_level"),
        "issue": risk.get("issue"),
        "suggestion": risk.get("suggestion"),
        "source_excerpt": _risk_source_excerpt(risk),
        "matched_clauses": (risk.get("matched_clauses") or [])[:5],
    }


def _risk_source_excerpt(risk: dict[str, Any]) -> str:
    for evidence in risk.get("evidence") or []:
        if isinstance(evidence, dict) and evidence.get("snippet"):
            return str(evidence.get("snippet"))
    matched_clauses = risk.get("matched_clauses") or []
    if matched_clauses and isinstance(matched_clauses[0], dict):
        return str(matched_clauses[0].get("text") or "")
    return str(risk.get("issue") or "")


def _unique_feedback_clauses(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clauses: list[dict[str, Any]] = []
    seen: set[str] = set()
    for risk in risks:
        for clause in risk.get("matched_clauses") or []:
            if not isinstance(clause, dict):
                continue
            clause_id = str(clause.get("id") or clause.get("title") or clause.get("text") or "")
            if not clause_id or clause_id in seen:
                continue
            seen.add(clause_id)
            clauses.append(
                {
                    "id": clause.get("id"),
                    "number": clause.get("number"),
                    "title": clause.get("title"),
                    "type": clause.get("type"),
                    "location": clause.get("location"),
                    "text": clause.get("text"),
                }
            )
    return clauses[:10]


def _summarize(contract: dict) -> dict:
    risks = contract.get("risks") or []
    return {
        "id": contract["id"],
        "name": contract["name"],
        "source": contract.get("source", ""),
        "status": contract.get("status", ""),
        "status_text": contract.get("status_text", ""),
        "created_at": contract.get("created_at", ""),
        "contract_type": contract.get("contract_type", ""),
        "review_strategy": (contract.get("review_strategy") or {}).get("name", ""),
        "flow_decision": (contract.get("flow_decision") or {}).get("decision", ""),
        "flow_strategy": ((contract.get("flow_decision") or {}).get("flow_strategy") or {}).get("name", ""),
        "risk_count": len(risks),
        "p0_count": sum(1 for risk in risks if risk.get("priority") == "P0"),
        "p1_count": sum(1 for risk in risks if risk.get("priority") == "P1"),
    }


def _hash_upload_file(file_obj) -> tuple[str, int]:
    hasher = hashlib.sha256()
    size = 0
    file_obj.seek(0)
    while chunk := file_obj.read(1024 * 1024):
        hasher.update(chunk)
        size += len(chunk)
    file_obj.seek(0)
    return hasher.hexdigest(), size


def _hash_path(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as file_obj:
        while chunk := file_obj.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def _find_contract_by_file_hash(file_hash: str) -> dict | None:
    if not file_hash:
        return None
    for contract in store.list_contracts():
        if contract.get("file_sha256") == file_hash:
            return contract
        file_path = contract.get("file_path")
        if not file_path:
            continue
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            continue
        try:
            if _hash_path(path) == file_hash:
                return contract
        except OSError:
            continue
    return None


def _model_to_dict(model: BaseModel) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _safe_filename(filename: str) -> str:
    name = Path(filename).name.strip().replace("\x00", "")
    for char in '\\/:*?"<>|':
        name = name.replace(char, "_")
    return name[:180]


def _public_agent_response(agent_item: dict) -> dict:
    model = dict(agent_item.get("model") or {})
    api_key = str(model.pop("api_key", "") or "")
    model["api_key_configured"] = bool(api_key)
    model["api_key_mask"] = f"{api_key[:4]}****{api_key[-4:]}" if len(api_key) > 8 else ("****" if api_key else "")
    return {**agent_item, "model": model}


FRONTEND_DIR = ROOT_DIR / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
