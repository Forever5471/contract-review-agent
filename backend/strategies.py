from __future__ import annotations

import json
import threading
from copy import deepcopy
from typing import Any

from .rules import list_rules
from .storage import DATA_DIR, now_iso


STRATEGIES_FILE = DATA_DIR / "strategies.json"
_LOCK = threading.RLock()


DEFAULT_STRATEGIES: list[dict[str, Any]] = [
    {
        "id": "strategy-sales",
        "name": "销售合同审核策略",
        "template_type": "销售合同",
        "description": "适用于产品销售、供货、买卖类合同，重点审查主体、付款、签章、生效、金额流程和违约责任。",
        "rule_ids": [
            "SL-GEN-003",
            "SL-GEN-004",
            "SL-GEN-010",
            "SL-GEN-012",
            "SL-GEN-014",
            "SL-ROLE-OFFICE-001",
            "SL-ROLE-LEGAL-002",
        ],
        "agent_instruction": "按销售合同策略审核：优先核对签约主体、标的/价款、付款和发票、交货验收、签章生效、违约责任。",
        "enabled": True,
    },
    {
        "id": "strategy-engineering",
        "name": "工程合同审核策略",
        "template_type": "工程合同",
        "description": "适用于工程、施工、外包类合同，重点审查安全协议、付款、生效、违约和重要合同流程。",
        "rule_ids": [
            "SL-GEN-003",
            "SL-GEN-004",
            "SL-GEN-010",
            "SL-GEN-012",
            "SL-GEN-014",
            "SL-TYPE-ENG-002",
            "SL-ROLE-OFFICE-001",
            "SL-ROLE-LEGAL-002",
        ],
        "agent_instruction": "按工程合同策略审核：除通用条款外，重点确认安全生产、施工外包责任、验收、工期和保险安排。",
        "enabled": True,
    },
    {
        "id": "strategy-general",
        "name": "通用合同审核策略",
        "template_type": "通用合同",
        "description": "兜底策略。合同类型或模板匹配不明确时，执行通用高价值规则。",
        "rule_ids": [
            "SL-GEN-003",
            "SL-GEN-004",
            "SL-GEN-010",
            "SL-GEN-012",
            "SL-GEN-014",
            "SL-ROLE-OFFICE-001",
            "SL-ROLE-LEGAL-002",
        ],
        "agent_instruction": "按通用合同策略审核：优先识别主体、金额、付款、生效签章、违约责任和是否需要人工确认。",
        "enabled": True,
    },
]


def list_strategies(include_disabled: bool = True) -> list[dict[str, Any]]:
    strategies = _load_strategies()
    if not include_disabled:
        strategies = [strategy for strategy in strategies if strategy.get("enabled", True)]
    return strategies


def get_strategy(strategy_id: str) -> dict[str, Any] | None:
    for strategy in _load_strategies():
        if strategy["id"] == strategy_id:
            return strategy
    return None


def save_strategy(payload: dict[str, Any], original_id: str | None = None) -> dict[str, Any]:
    strategy = normalize_strategy(payload)
    with _LOCK:
        strategies = _load_strategies()
        lookup_id = original_id or strategy["id"]
        for existing in strategies:
            if existing["id"] == strategy["id"] and existing["id"] != lookup_id:
                raise ValueError(f"审核策略编号 {strategy['id']} 已存在")
        for index, existing in enumerate(strategies):
            if existing["id"] == lookup_id:
                strategy["created_at"] = existing.get("created_at") or now_iso()
                strategy["updated_at"] = now_iso()
                strategies[index] = strategy
                _write_strategies(strategies)
                return strategy
        strategy["created_at"] = now_iso()
        strategy["updated_at"] = now_iso()
        strategies.append(strategy)
        _write_strategies(strategies)
        return strategy


def delete_strategy(strategy_id: str) -> None:
    with _LOCK:
        strategies = _load_strategies()
        next_strategies = [strategy for strategy in strategies if strategy["id"] != strategy_id]
        if len(next_strategies) == len(strategies):
            raise KeyError(strategy_id)
        _write_strategies(next_strategies)


def reset_strategies() -> list[dict[str, Any]]:
    strategies = [normalize_strategy(strategy) for strategy in deepcopy(DEFAULT_STRATEGIES)]
    now = now_iso()
    for strategy in strategies:
        strategy["created_at"] = now
        strategy["updated_at"] = now
    _write_strategies(strategies)
    return strategies


def match_strategy(contract_type: str, template_match: dict[str, Any] | None = None) -> dict[str, Any]:
    strategies = list_strategies(include_disabled=False)
    matched_text = " ".join(
        str(item or "")
        for item in [
            contract_type,
            (template_match or {}).get("template_name"),
        ]
    )
    for strategy in strategies:
        template_type = str(strategy.get("template_type") or "")
        if template_type and template_type in matched_text:
            return _with_rule_summary(strategy)
    if "销售" in matched_text:
        found = _find_by_template(strategies, "销售合同")
        if found:
            return _with_rule_summary(found)
    if any(keyword in matched_text for keyword in ["工程", "施工", "外包"]):
        found = _find_by_template(strategies, "工程合同")
        if found:
            return _with_rule_summary(found)
    found = _find_by_template(strategies, "通用合同")
    if found:
        return _with_rule_summary(found)
    return _with_rule_summary(strategies[0]) if strategies else _with_rule_summary(normalize_strategy(DEFAULT_STRATEGIES[-1]))


def normalize_strategy(payload: dict[str, Any]) -> dict[str, Any]:
    strategy_id = str(payload.get("id") or "").strip()
    name = str(payload.get("name") or "").strip()
    template_type = str(payload.get("template_type") or "").strip()
    if not strategy_id:
        raise ValueError("审核策略编号不能为空")
    if not name:
        raise ValueError("审核策略名称不能为空")
    if not template_type:
        raise ValueError("合同模板类型不能为空")
    return {
        "id": strategy_id,
        "name": name,
        "template_type": template_type,
        "description": str(payload.get("description") or "").strip(),
        "rule_ids": _normalize_list(payload.get("rule_ids")),
        "agent_instruction": str(payload.get("agent_instruction") or "").strip(),
        "enabled": bool(payload.get("enabled", True)),
        "created_at": payload.get("created_at") or "",
        "updated_at": payload.get("updated_at") or "",
    }


def _with_rule_summary(strategy: dict[str, Any]) -> dict[str, Any]:
    rules_by_id = {rule["id"]: rule for rule in list_rules(include_disabled=True)}
    rules = [rules_by_id[rule_id] for rule_id in strategy.get("rule_ids", []) if rule_id in rules_by_id]
    missing_rule_ids = [rule_id for rule_id in strategy.get("rule_ids", []) if rule_id not in rules_by_id]
    return {
        **deepcopy(strategy),
        "rules": [
            {
                "id": rule["id"],
                "name": rule["name"],
                "mode": rule["mode"],
                "priority": rule["priority"],
                "risk_level": rule["risk_level"],
                "enabled": rule.get("enabled", True),
            }
            for rule in rules
        ],
        "missing_rule_ids": missing_rule_ids,
    }


def _find_by_template(strategies: list[dict[str, Any]], template_type: str) -> dict[str, Any] | None:
    for strategy in strategies:
        if strategy.get("template_type") == template_type:
            return strategy
    return None


def _normalize_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [item.strip() for item in value.replace("，", ",").split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _load_strategies() -> list[dict[str, Any]]:
    with _LOCK:
        if not STRATEGIES_FILE.exists():
            return [normalize_strategy(strategy) for strategy in deepcopy(DEFAULT_STRATEGIES)]
        data = json.loads(STRATEGIES_FILE.read_text(encoding="utf-8"))
        raw_strategies = data.get("strategies", data if isinstance(data, list) else [])
        return [normalize_strategy(strategy) for strategy in raw_strategies]


def _write_strategies(strategies: list[dict[str, Any]]) -> None:
    with _LOCK:
        STRATEGIES_FILE.write_text(
            json.dumps({"strategies": strategies}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
