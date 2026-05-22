from __future__ import annotations

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .agent import ContractReviewAgent
from .agent_skills.contract_intake import ContractIntakeSkill
from .llm import get_llm_status
from .rules import RULES
from .storage import JsonStore, ROOT_DIR, now_iso


app = FastAPI(title="Contract Review Agent MVP")
store = JsonStore()
intake_skill = ContractIntakeSkill()
agent = ContractReviewAgent(store)


class HumanReviewRequest(BaseModel):
    action: str
    opinion: str = ""
    reviewer: str = ""

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
    return get_llm_status()


@app.get("/api/rules/stats")
def rule_stats() -> dict:
    high_priorities = {"P0", "P1"}
    general_priorities = {"P2", "P3"}
    high_rules = [rule for rule in RULES if rule.get("priority") in high_priorities]
    general_rules = [rule for rule in RULES if rule.get("priority") in general_priorities]
    return {
        "high_risk_rules": len(high_rules),
        "general_risk_rules": len(general_rules),
        "total_rules": len(RULES),
        "priority_counts": {
            priority: sum(1 for rule in RULES if rule.get("priority") == priority)
            for priority in ["P0", "P1", "P2", "P3"]
        },
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
    intake_result = intake_skill.run_upload(
        file.file,
        file.filename or "contract",
        source,
        business_dept,
        initiator,
        store,
    )
    contract = intake_result["data"]["contract"]
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
        "risk_count": len(risks),
        "p0_count": sum(1 for risk in risks if risk.get("priority") == "P0"),
        "p1_count": sum(1 for risk in risks if risk.get("priority") == "P1"),
    }


FRONTEND_DIR = ROOT_DIR / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
