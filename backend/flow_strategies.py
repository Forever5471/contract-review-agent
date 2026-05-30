from __future__ import annotations

import json
import threading
from copy import deepcopy
from typing import Any

from .storage import DATA_DIR, now_iso
from .strategies import list_strategies


FLOW_STRATEGIES_FILE = DATA_DIR / "flow_strategies.json"
_LOCK = threading.RLock()


DEFAULT_FLOW_STRATEGIES: list[dict[str, Any]] = [
    {
        "id": "flow-standard-contracts",
        "name": "标准合同流转策略",
        "description": "适用于销售、采购和通用合同。无重大风险时允许自动进入后续流程，存在高风险时进入人工确认。",
        "review_strategy_ids": ["strategy-sales", "strategy-general"],
        "auto_pass_max_p0": 0,
        "auto_pass_max_p1": 0,
        "auto_pass_max_general": 2,
        "auto_pass_max_amount": 100000,
        "human_confirm_min_amount": 100000,
        "human_confirm_min_p1": 1,
        "human_confirm_min_general": 3,
        "need_revision_min_p0": 1,
        "blocked_rule_ids": [],
        "need_revision_rule_ids": ["SL-GEN-012"],
        "enabled": True,
    },
    {
        "id": "flow-high-risk-contracts",
        "name": "高风险合同流转策略",
        "description": "适用于工程、安全、外包等高风险合同。金额、P1 风险或关键规则命中时必须人工确认或退回修改。",
        "review_strategy_ids": ["strategy-engineering"],
        "auto_pass_max_p0": 0,
        "auto_pass_max_p1": 0,
        "auto_pass_max_general": 0,
        "auto_pass_max_amount": 50000,
        "human_confirm_min_amount": 50000,
        "human_confirm_min_p1": 1,
        "human_confirm_min_general": 1,
        "need_revision_min_p0": 1,
        "blocked_rule_ids": [],
        "need_revision_rule_ids": ["SL-GEN-012", "SL-TYPE-ENG-002"],
        "enabled": True,
    },
]


DECISION_STATUS = {
    "AutoPass": ("Completed", "审核完成：自动通过"),
    "NeedHumanConfirm": ("NeedHumanConfirm", "待人工确认"),
    "NeedRevision": ("NeedRevision", "需退回修改"),
    "Blocked": ("Blocked", "禁止流转"),
}


def list_flow_strategies(include_disabled: bool = True) -> list[dict[str, Any]]:
    items = [_with_review_strategy_summary(item) for item in _load_flow_strategies()]
    if not include_disabled:
        items = [item for item in items if item.get("enabled", True)]
    return items


def get_flow_strategy(flow_strategy_id: str) -> dict[str, Any] | None:
    for item in _load_flow_strategies():
        if item["id"] == flow_strategy_id:
            return _with_review_strategy_summary(item)
    return None


def save_flow_strategy(payload: dict[str, Any], original_id: str | None = None) -> dict[str, Any]:
    item = normalize_flow_strategy(payload)
    with _LOCK:
        items = _load_flow_strategies()
        lookup_id = original_id or item["id"]
        for existing in items:
            if existing["id"] == item["id"] and existing["id"] != lookup_id:
                raise ValueError(f"审核流转策略编号 {item['id']} 已存在")
        for index, existing in enumerate(items):
            if existing["id"] == lookup_id:
                item["created_at"] = existing.get("created_at") or now_iso()
                item["updated_at"] = now_iso()
                items[index] = item
                _write_flow_strategies(items)
                return _with_review_strategy_summary(item)
        item["created_at"] = now_iso()
        item["updated_at"] = now_iso()
        items.append(item)
        _write_flow_strategies(items)
        return _with_review_strategy_summary(item)


def delete_flow_strategy(flow_strategy_id: str) -> None:
    with _LOCK:
        items = _load_flow_strategies()
        next_items = [item for item in items if item["id"] != flow_strategy_id]
        if len(next_items) == len(items):
            raise KeyError(flow_strategy_id)
        _write_flow_strategies(next_items)


def reset_flow_strategies() -> list[dict[str, Any]]:
    items = [normalize_flow_strategy(item) for item in deepcopy(DEFAULT_FLOW_STRATEGIES)]
    now = now_iso()
    for item in items:
        item["created_at"] = now
        item["updated_at"] = now
    _write_flow_strategies(items)
    return [_with_review_strategy_summary(item) for item in items]


def match_flow_strategy(review_strategy: dict[str, Any] | None) -> dict[str, Any]:
    review_strategy_id = str((review_strategy or {}).get("id") or "").strip()
    items = list_flow_strategies(include_disabled=False)
    for item in items:
        if review_strategy_id and review_strategy_id in item.get("review_strategy_ids", []):
            return item
    return items[0] if items else _with_review_strategy_summary(normalize_flow_strategy(DEFAULT_FLOW_STRATEGIES[0]))


def decide_contract_flow(
    contract: dict[str, Any],
    risks: list[dict[str, Any]],
    report: dict[str, Any],
    review_strategy: dict[str, Any] | None,
) -> dict[str, Any]:
    flow_strategy = match_flow_strategy(review_strategy)
    counts = _risk_counts(risks, report)
    amount = _to_float((contract.get("fields") or {}).get("max_amount"), 0)
    rule_ids = {str(risk.get("rule_id") or "") for risk in risks}

    blocked_hit = sorted(rule_ids & set(flow_strategy.get("blocked_rule_ids") or []))
    revision_hit = sorted(rule_ids & set(flow_strategy.get("need_revision_rule_ids") or []))
    if blocked_hit:
        return _decision("Blocked", flow_strategy, f"命中禁止流转规则：{', '.join(blocked_hit)}", counts, amount)
    if counts["P0"] >= int(flow_strategy.get("need_revision_min_p0", 1)) and int(flow_strategy.get("need_revision_min_p0", 1)) > 0:
        return _decision("NeedRevision", flow_strategy, f"命中 {counts['P0']} 项 P0 严重风险。", counts, amount)
    if revision_hit:
        return _decision("NeedRevision", flow_strategy, f"命中需退回修改规则：{', '.join(revision_hit)}", counts, amount)

    general_count = counts["P2"] + counts["P3"]
    if counts["P1"] >= int(flow_strategy.get("human_confirm_min_p1", 1)) and int(flow_strategy.get("human_confirm_min_p1", 1)) > 0:
        return _decision("NeedHumanConfirm", flow_strategy, f"命中 {counts['P1']} 项 P1 高风险。", counts, amount)
    if general_count >= int(flow_strategy.get("human_confirm_min_general", 3)) and int(flow_strategy.get("human_confirm_min_general", 3)) > 0:
        return _decision("NeedHumanConfirm", flow_strategy, f"一般风险数量达到 {general_count} 项。", counts, amount)
    if amount >= float(flow_strategy.get("human_confirm_min_amount", 100000) or 0) and float(flow_strategy.get("human_confirm_min_amount", 100000) or 0) > 0:
        return _decision("NeedHumanConfirm", flow_strategy, f"合同金额 {amount:,.2f} 达到人工确认阈值。", counts, amount)
    incomplete_count = int(report.get("incomplete_rule_count") or len(report.get("incomplete_rules") or []))
    if incomplete_count > 0:
        return _decision("NeedHumanConfirm", flow_strategy, f"有 {incomplete_count} 条规则未完成判断，需人工确认或重试后再流转。", counts, amount)

    can_auto_pass = (
        counts["P0"] <= int(flow_strategy.get("auto_pass_max_p0", 0))
        and counts["P1"] <= int(flow_strategy.get("auto_pass_max_p1", 0))
        and general_count <= int(flow_strategy.get("auto_pass_max_general", 0))
        and amount <= float(flow_strategy.get("auto_pass_max_amount", 0) or 0)
    )
    if can_auto_pass:
        return _decision("AutoPass", flow_strategy, "满足自动通过条件。", counts, amount)
    return _decision("NeedHumanConfirm", flow_strategy, "未满足自动通过条件，进入人工确认。", counts, amount)


def normalize_flow_strategy(payload: dict[str, Any]) -> dict[str, Any]:
    item_id = str(payload.get("id") or "").strip()
    name = str(payload.get("name") or "").strip()
    if not item_id:
        raise ValueError("审核流转策略编号不能为空")
    if not name:
        raise ValueError("审核流转策略名称不能为空")
    return {
        "id": item_id,
        "name": name,
        "description": str(payload.get("description") or "").strip(),
        "review_strategy_ids": _normalize_list(payload.get("review_strategy_ids")),
        "auto_pass_max_p0": _to_int(payload.get("auto_pass_max_p0"), 0),
        "auto_pass_max_p1": _to_int(payload.get("auto_pass_max_p1"), 0),
        "auto_pass_max_general": _to_int(payload.get("auto_pass_max_general"), 2),
        "auto_pass_max_amount": _to_float(payload.get("auto_pass_max_amount"), 100000),
        "human_confirm_min_amount": _to_float(payload.get("human_confirm_min_amount"), 100000),
        "human_confirm_min_p1": _to_int(payload.get("human_confirm_min_p1"), 1),
        "human_confirm_min_general": _to_int(payload.get("human_confirm_min_general"), 3),
        "need_revision_min_p0": _to_int(payload.get("need_revision_min_p0"), 1),
        "blocked_rule_ids": _normalize_list(payload.get("blocked_rule_ids")),
        "need_revision_rule_ids": _normalize_list(payload.get("need_revision_rule_ids")),
        "enabled": bool(payload.get("enabled", True)),
        "created_at": payload.get("created_at") or "",
        "updated_at": payload.get("updated_at") or "",
    }


def _decision(decision: str, flow_strategy: dict[str, Any], reason: str, counts: dict[str, int], amount: float) -> dict[str, Any]:
    status, status_text = DECISION_STATUS[decision]
    next_action = {
        "AutoPass": "可自动进入后续审批、用印或归档流程。",
        "NeedHumanConfirm": "需业务、法务、财务或相关责任人确认后再流转。",
        "NeedRevision": "需退回经办人补充或修订后重新提交审核。",
        "Blocked": "命中禁止流转条件，需解除风险后重新发起。",
    }[decision]
    return {
        "decision": decision,
        "status": status,
        "status_text": status_text,
        "reason": reason,
        "next_action": next_action,
        "auto_flow_allowed": decision == "AutoPass",
        "flow_strategy": {
            "id": flow_strategy.get("id"),
            "name": flow_strategy.get("name"),
            "review_strategy_ids": flow_strategy.get("review_strategy_ids") or [],
        },
        "risk_counts": counts,
        "amount": amount,
    }


def _risk_counts(risks: list[dict[str, Any]], report: dict[str, Any]) -> dict[str, int]:
    counts = {key: 0 for key in ["P0", "P1", "P2", "P3"]}
    report_counts = report.get("risk_counts") or {}
    for key in counts:
        counts[key] = int(report_counts.get(key) or 0)
    if any(counts.values()) or not risks:
        return counts
    for risk in risks:
        priority = risk.get("priority")
        if priority in counts:
            counts[priority] += 1
    return counts


def _with_review_strategy_summary(item: dict[str, Any]) -> dict[str, Any]:
    strategies_by_id = {strategy["id"]: strategy for strategy in list_strategies()}
    return {
        **deepcopy(item),
        "review_strategies": [
            {
                "id": strategy["id"],
                "name": strategy["name"],
                "template_type": strategy["template_type"],
            }
            for strategy_id in item.get("review_strategy_ids", [])
            for strategy in [strategies_by_id.get(strategy_id)]
            if strategy
        ],
    }


def _normalize_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [item.strip() for item in value.replace("，", ",").split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_flow_strategies() -> list[dict[str, Any]]:
    with _LOCK:
        if not FLOW_STRATEGIES_FILE.exists():
            return [normalize_flow_strategy(item) for item in deepcopy(DEFAULT_FLOW_STRATEGIES)]
        data = json.loads(FLOW_STRATEGIES_FILE.read_text(encoding="utf-8"))
        raw_items = data.get("flow_strategies", data if isinstance(data, list) else [])
        return [normalize_flow_strategy(item) for item in raw_items]


def _write_flow_strategies(items: list[dict[str, Any]]) -> None:
    with _LOCK:
        FLOW_STRATEGIES_FILE.write_text(
            json.dumps({"flow_strategies": items}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
