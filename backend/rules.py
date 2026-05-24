from __future__ import annotations

import json
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

from .storage import DATA_DIR, now_iso


RULES_FILE = DATA_DIR / "rules.json"
_LOCK = threading.RLock()


DEFAULT_INPUT_PARAMS = [
    {
        "display_name": "合同主体列表",
        "name": "parties",
        "type": "array",
        "description": "从合同中抽取甲方、乙方、买方、卖方、发包方、承包方等签约主体名称。",
    },
]


DEFAULT_OUTPUT_PARAMS = [
    {
        "display_name": "是否通过",
        "name": "passed",
        "type": "boolean",
        "description": "规则判断是否通过。",
    },
    {
        "display_name": "风险问题",
        "name": "issue",
        "type": "string",
        "description": "未通过时面向审核人员展示的问题描述。",
    },
    {
        "display_name": "修改建议",
        "name": "suggestion",
        "type": "string",
        "description": "未通过时给出的可执行修改建议。",
    },
    {
        "display_name": "判断依据",
        "name": "evidence",
        "type": "array",
        "description": "支撑判断的字段、关键词或制度依据。",
    },
]


DEFAULT_RULES: list[dict[str, Any]] = [
    {
        "id": "SL-GEN-003",
        "name": "首页与签章页主体完整性",
        "mode": "脚本模式",
        "priority": "P2",
        "risk_level": "一般风险",
        "scope": ["通用规则"],
        "description": "合同应出现双方主体信息，并在签章/签字处体现。",
        "enabled": True,
        "script": """passed = len(parties or []) >= 2
issue = "合同主体信息疑似不完整。"
suggestion = "补充甲乙双方完整名称，并核对首页、正文和签章页一致性。"
evidence = [{"type": "input_param", "field": "parties", "value": parties}]""",
        "instruction": "",
        "input_params": [
            {
                "display_name": "合同主体列表",
                "name": "parties",
                "type": "array",
                "description": "从合同中抽取甲方、乙方、买方、卖方、发包方、承包方等签约主体名称。",
            },
        ],
        "output_params": DEFAULT_OUTPUT_PARAMS,
    },
    {
        "id": "SL-GEN-004",
        "name": "我方主体名称与角色一致性",
        "mode": "脚本模式",
        "priority": "P1",
        "risk_level": "高风险",
        "scope": ["通用规则"],
        "description": "识别我方主体是否为盛龙矿业或相关主体。",
        "enabled": True,
        "script": """our_keywords = ["盛龙矿业", "洛阳盛龙", "栾川龙宇", "龙宇钼业"]
subject_text = str(our_party_name or "")
passed = any(keyword in subject_text for keyword in our_keywords) or any(keyword in text for keyword in our_keywords)
issue = "未明显识别到我方主体名称，可能存在主体错误或非标准文本。"
suggestion = "核对我方签约主体是否为授权主体，并确保签章主体一致。"
evidence = [{"type": "input_param", "field": "our_party_name", "value": our_party_name}, {"type": "keyword", "expected": our_keywords}]""",
        "instruction": "",
        "input_params": [
            {
                "display_name": "我方主体名称",
                "name": "our_party_name",
                "type": "string",
                "description": "合同中代表我方或本公司一方的签约主体名称。",
            },
        ],
        "output_params": DEFAULT_OUTPUT_PARAMS,
    },
    {
        "id": "SL-GEN-010",
        "name": "付款方式和付款条件完整性",
        "mode": "指令模式",
        "priority": "P1",
        "risk_level": "高风险",
        "scope": ["通用规则", "财务规则"],
        "description": "合同应明确付款方式、节点、条件、发票要求。",
        "enabled": True,
        "script": "",
        "instruction": "结合合同付款条款、发票税率、付款节点和结算资料要求，判断付款安排是否完整、清晰、可执行。",
        "input_params": [
            {
                "display_name": "付款条款",
                "name": "payment_clause",
                "type": "string",
                "description": "合同中关于付款方式、付款节点、付款条件、结算资料的条款原文或摘要。",
            },
            {
                "display_name": "发票条款",
                "name": "invoice_clause",
                "type": "string",
                "description": "合同中关于发票类型、税率、含税价、开票要求的条款原文或摘要。",
            },
        ],
        "output_params": DEFAULT_OUTPUT_PARAMS,
    },
    {
        "id": "SL-GEN-012",
        "name": "付款不得早于合同生效/审批",
        "mode": "脚本模式",
        "priority": "P0",
        "risk_level": "高风险",
        "scope": ["通用规则", "财务规则"],
        "description": "识别生效前付款、审批前履行等重大风险。",
        "enabled": True,
        "script": """risky_patterns = ["生效前支付", "签订前支付", "审批前支付", "未生效前支付"]
payment_text = str(payment_timing_clause or text)
passed = not any(pattern in payment_text for pattern in risky_patterns)
issue = "发现付款可能早于合同生效或审批完成。"
suggestion = "将付款条件调整为合同审批完成且双方签字盖章生效后支付。"
evidence = [{"type": "pattern", "value": pattern} for pattern in risky_patterns if pattern in payment_text]""",
        "instruction": "",
        "input_params": [
            {
                "display_name": "付款时点条款",
                "name": "payment_timing_clause",
                "type": "string",
                "description": "合同中描述付款发生时间、付款前置条件、生效或审批要求的条款。",
            },
        ],
        "output_params": DEFAULT_OUTPUT_PARAMS,
    },
    {
        "id": "SL-GEN-014",
        "name": "签章与生效条款校验",
        "mode": "脚本模式",
        "priority": "P1",
        "risk_level": "高风险",
        "scope": ["通用规则", "用印规则"],
        "description": "合同应明确签字盖章后生效。",
        "enabled": True,
        "script": """passed = bool(has_effective_clause) and bool(has_seal_clause)
issue = "签章或生效条款不完整。"
suggestion = "补充“双方签字并盖章后生效”等明确表述。"
evidence = [
    {"type": "input_param", "field": "has_effective_clause", "value": has_effective_clause},
    {"type": "input_param", "field": "has_seal_clause", "value": has_seal_clause},
]""",
        "instruction": "",
        "input_params": [
            {
                "display_name": "是否有生效条款",
                "name": "has_effective_clause",
                "type": "boolean",
                "description": "合同是否明确约定生效条件，如签字、盖章、审批完成后生效。",
            },
            {
                "display_name": "是否有签章条款",
                "name": "has_seal_clause",
                "type": "boolean",
                "description": "合同是否明确要求双方签字、盖章、公章或授权代表签署。",
            },
        ],
        "output_params": DEFAULT_OUTPUT_PARAMS,
    },
    {
        "id": "SL-ROLE-OFFICE-001",
        "name": "一般/重要合同流程识别",
        "mode": "脚本模式",
        "priority": "P2",
        "risk_level": "高风险",
        "scope": ["角色规则", "归口管理"],
        "description": "根据金额识别一般合同、重要合同和会议评审要求。",
        "enabled": True,
        "script": """amount = max_amount or 0
passed = True
issue = ""
suggestion = ""
if amount >= 100_000_000:
    issue = "合同金额达到 1 亿元以上，需会议评审和重点会签。"
    suggestion = "触发重要合同会议评审流程。"
    passed = False
elif amount >= 300_000:
    issue = "合同金额达到重要合同阈值，需按重要合同流程审核。"
    suggestion = "触发重要合同审批和会签角色。"
    passed = False
evidence = [{"type": "field", "field": "max_amount", "value": amount}]""",
        "instruction": "",
        "input_params": [
            {
                "display_name": "合同最高金额",
                "name": "max_amount",
                "type": "number",
                "description": "从合同金额、总价、暂估价、结算上限中抽取的最高人民币金额。",
            },
        ],
        "output_params": DEFAULT_OUTPUT_PARAMS,
    },
    {
        "id": "SL-TYPE-ENG-002",
        "name": "工程安全管理协议触发",
        "mode": "脚本模式",
        "priority": "P0",
        "risk_level": "高风险",
        "scope": ["合同类型规则", "安全环保"],
        "description": "工程、施工、外包类合同应关联安全管理协议。",
        "enabled": True,
        "script": """is_engineering = "工程" in contract_type or any(kw in text for kw in ["施工", "承包", "外包"])
passed = (not is_engineering) or bool(has_safety_clause)
issue = "工程/施工/外包类合同未明显关联安全管理责任或安全协议。"
suggestion = "补充工程安全管理协议或明确安全生产责任、事故责任和保险要求。"
evidence = [{"type": "input_param", "field": "has_safety_clause", "value": has_safety_clause}] + rag.run("工程 安全 管理 协议 安全生产", top_k=2)["data"]["results"]""",
        "instruction": "",
        "input_params": [
            {
                "display_name": "是否有安全条款",
                "name": "has_safety_clause",
                "type": "boolean",
                "description": "合同是否包含安全生产、安全管理、事故责任、环保或安全协议相关条款。",
            },
        ],
        "output_params": DEFAULT_OUTPUT_PARAMS,
    },
    {
        "id": "SL-ROLE-LEGAL-002",
        "name": "违约责任具体量化",
        "mode": "指令模式",
        "priority": "P1",
        "risk_level": "高风险",
        "scope": ["角色规则", "法务规则"],
        "description": "违约情形、违约金、解除权、损失范围应具体明确。",
        "enabled": True,
        "script": "",
        "instruction": "结合违约责任条款，判断违约情形、违约金、赔偿范围、解除权和维权费用承担是否具体可执行。",
        "input_params": [
            {
                "display_name": "违约责任条款",
                "name": "breach_clause",
                "type": "string",
                "description": "合同中关于违约情形、违约金、赔偿范围、解除权、维权费用承担的条款原文或摘要。",
            },
        ],
        "output_params": DEFAULT_OUTPUT_PARAMS,
    },
]


def list_rules(include_disabled: bool = True) -> list[dict[str, Any]]:
    rules = _load_rules()
    if not include_disabled:
        rules = [rule for rule in rules if rule.get("enabled", True)]
    return rules


def get_rule(rule_id: str) -> dict[str, Any] | None:
    for rule in _load_rules():
        if rule["id"] == rule_id:
            return rule
    return None


def save_rule(payload: dict[str, Any], original_id: str | None = None) -> dict[str, Any]:
    rule = normalize_rule(payload)
    with _LOCK:
        rules = _load_rules()
        lookup_id = original_id or rule["id"]
        for existing in rules:
            if existing["id"] == rule["id"] and existing["id"] != lookup_id:
                raise ValueError(f"规则编号 {rule['id']} 已存在")
        for index, existing in enumerate(rules):
            if existing["id"] == lookup_id:
                rule["created_at"] = existing.get("created_at") or now_iso()
                rule["updated_at"] = now_iso()
                rules[index] = rule
                _write_rules(rules)
                return rule
        rule["created_at"] = now_iso()
        rule["updated_at"] = now_iso()
        rules.append(rule)
        _write_rules(rules)
        return rule


def delete_rule(rule_id: str) -> None:
    with _LOCK:
        rules = _load_rules()
        next_rules = [rule for rule in rules if rule["id"] != rule_id]
        if len(next_rules) == len(rules):
            raise KeyError(rule_id)
        _write_rules(next_rules)


def reset_rules() -> list[dict[str, Any]]:
    rules = [normalize_rule(rule) for rule in deepcopy(DEFAULT_RULES)]
    now = now_iso()
    for rule in rules:
        rule["created_at"] = now
        rule["updated_at"] = now
    _write_rules(rules)
    return rules


def normalize_rule(payload: dict[str, Any]) -> dict[str, Any]:
    rule_id = str(payload.get("id") or "").strip()
    name = str(payload.get("name") or "").strip()
    if not rule_id:
        raise ValueError("规则编号不能为空")
    if not name:
        raise ValueError("规则名称不能为空")

    mode = str(payload.get("mode") or "脚本模式").strip()
    if mode not in {"脚本模式", "指令模式"}:
        raise ValueError("规则模式仅支持脚本模式或指令模式")

    priority = str(payload.get("priority") or "P2").strip().upper()
    if priority not in {"P0", "P1", "P2", "P3"}:
        raise ValueError("优先级仅支持 P0、P1、P2、P3")

    scope = payload.get("scope") or []
    if isinstance(scope, str):
        scope = [item.strip() for item in scope.replace("，", ",").split(",") if item.strip()]
    elif isinstance(scope, list):
        scope = [str(item).strip() for item in scope if str(item).strip()]
    else:
        scope = []
    risk_level = str(payload.get("risk_level") or "").strip() or _default_risk_level(priority)
    if risk_level not in {"高风险", "一般风险"}:
        risk_level = "高风险" if priority in {"P0", "P1"} else "一般风险"

    return {
        "id": rule_id,
        "name": name,
        "mode": mode,
        "priority": priority,
        "risk_level": risk_level,
        "scope": scope,
        "description": str(payload.get("description") or "").strip(),
        "enabled": bool(payload.get("enabled", True)),
        "script": str(payload.get("script") or "").strip(),
        "instruction": str(payload.get("instruction") or "").strip(),
        "input_params": _normalize_params(payload.get("input_params") or DEFAULT_INPUT_PARAMS),
        "output_params": _normalize_params(payload.get("output_params") or DEFAULT_OUTPUT_PARAMS),
        "created_at": payload.get("created_at") or "",
        "updated_at": payload.get("updated_at") or "",
    }


def _normalize_params(params: Any) -> list[dict[str, str]]:
    if not isinstance(params, list):
        return []
    normalized = []
    for param in params:
        if not isinstance(param, dict):
            continue
        name = str(param.get("name") or "").strip()
        if not name:
            continue
        normalized.append(
            {
                "display_name": str(param.get("display_name") or "").strip() or name,
                "name": name,
                "type": str(param.get("type") or "string").strip(),
                "description": str(param.get("description") or "").strip(),
            }
        )
    return normalized


def _default_risk_level(priority: str) -> str:
    if priority in {"P0", "P1"}:
        return "高风险"
    return "一般风险"


def _load_rules() -> list[dict[str, Any]]:
    with _LOCK:
        if not RULES_FILE.exists():
            return [normalize_rule(rule) for rule in deepcopy(DEFAULT_RULES)]
        data = json.loads(RULES_FILE.read_text(encoding="utf-8"))
        raw_rules = data.get("rules", data if isinstance(data, list) else [])
        return [normalize_rule(rule) for rule in raw_rules]


def _write_rules(rules: list[dict[str, Any]]) -> None:
    with _LOCK:
        RULES_FILE.write_text(
            json.dumps({"rules": rules}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


RULES = DEFAULT_RULES
