from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Any

from ...storage import JsonStore, UPLOAD_DIR, now_iso


class ContractIntakeSkill:
    name = "ContractIntakeSkill"
    version = "0.3.0"

    def run_upload(
        self,
        file_obj: BinaryIO,
        file_name: str,
        source: str,
        business_dept: str,
        initiator: str,
        store: JsonStore,
    ) -> dict[str, Any]:
        contract_id = uuid.uuid4().hex[:12]
        safe_name = Path(file_name or "contract").name
        target = UPLOAD_DIR / f"{contract_id}_{safe_name}"
        with target.open("wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)

        contract = {
            "id": contract_id,
            "name": safe_name,
            "file_name": safe_name,
            "file_path": str(target),
            "source": source or "upload",
            "business_dept": business_dept,
            "initiator": initiator,
            "status": "Pending",
            "status_text": "等待审核",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "contract_type": "",
            "fields": {},
            "risks": [],
            "report": None,
            "review": {
                "events": [
                    {
                        "time": now_iso(),
                        "phase": "Intake",
                        "event_type": "skill_completed",
                        "message": "合同已入库，等待主审查 Agent 执行审核链路。",
                        "visible_to_user": True,
                        "skill_name": self.name,
                        "skill_version": self.version,
                    }
                ]
            },
        }
        store.upsert_contract(contract)
        stored_ok = store.get_contract(contract_id) is not None
        confidence_detail = self._calculate_confidence(target, safe_name, contract, stored_ok)
        contract["intake_confidence_detail"] = confidence_detail
        store.upsert_contract(contract)
        warnings = self._build_warnings(target, confidence_detail)
        return {
            "skill_name": self.name,
            "skill_version": self.version,
            "status": "success",
            "confidence": confidence_detail["overall"],
            "data": {"contract": contract},
            "evidence": [
                {
                    "type": "file",
                    "source": safe_name,
                    "size": target.stat().st_size if target.exists() else 0,
                    "suffix": target.suffix.lower(),
                }
            ],
            "warnings": warnings,
        }

    def _calculate_confidence(
        self,
        target: Path,
        safe_name: str,
        contract: dict[str, Any],
        stored_ok: bool,
    ) -> dict[str, Any]:
        supported_suffixes = {".docx", ".doc", ".pdf", ".txt", ".md"}
        file_exists = target.exists()
        file_size = target.stat().st_size if file_exists else 0
        file_score = min(1.0, file_size / 1024) if file_size else 0.0
        suffix_score = 1.0 if target.suffix.lower() in supported_suffixes else (0.35 if target.suffix else 0.0)
        metadata_values = [
            safe_name,
            contract.get("source"),
            contract.get("business_dept"),
            contract.get("initiator"),
        ]
        metadata_score = sum(1 for value in metadata_values if str(value or "").strip()) / len(metadata_values)
        persistence_score = 1.0 if stored_ok else 0.0
        overall = (
            file_score * 0.35
            + suffix_score * 0.20
            + metadata_score * 0.20
            + persistence_score * 0.25
        )
        return {
            "overall": round(max(0.1, min(0.98, overall)), 2),
            "file_size_signal": round(file_score, 2),
            "suffix_support": round(suffix_score, 2),
            "metadata_completeness": round(metadata_score, 2),
            "persistence_check": round(persistence_score, 2),
        }

    def _build_warnings(self, target: Path, confidence_detail: dict[str, Any]) -> list[str]:
        warnings = []
        if confidence_detail["file_size_signal"] <= 0:
            warnings.append("合同文件为空或未成功落盘。")
        if confidence_detail["suffix_support"] < 0.8:
            warnings.append("合同文件格式不在当前解析链路的优先支持范围内。")
        if confidence_detail["metadata_completeness"] < 0.75:
            warnings.append("合同入库元数据不完整，后续角色审核路由可能需要人工补充。")
        if not target.exists():
            warnings.append("合同文件入库后未通过落盘校验。")
        return warnings
