from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = ROOT_DIR.parent
DATA_DIR = ROOT_DIR / "data"
UPLOAD_DIR = ROOT_DIR / "uploads"
STORE_FILE = DATA_DIR / "store.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class JsonStore:
    def __init__(self, path: Path = STORE_FILE):
        self.path = path
        self._lock = threading.RLock()
        if not path.exists():
            self._write({"contracts": []})

    def _read(self) -> dict[str, Any]:
        with self._lock:
            return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        with self._lock:
            self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def list_contracts(self) -> list[dict[str, Any]]:
        data = self._read()
        return sorted(data["contracts"], key=lambda item: item["created_at"], reverse=True)

    def get_contract(self, contract_id: str) -> dict[str, Any] | None:
        for contract in self._read()["contracts"]:
            if contract["id"] == contract_id:
                return contract
        return None

    def upsert_contract(self, contract: dict[str, Any]) -> None:
        data = self._read()
        contracts = data["contracts"]
        for index, existing in enumerate(contracts):
            if existing["id"] == contract["id"]:
                contracts[index] = contract
                self._write(data)
                return
        contracts.append(contract)
        self._write(data)

    def update_contract(self, contract_id: str, **updates: Any) -> dict[str, Any]:
        data = self._read()
        for contract in data["contracts"]:
            if contract["id"] == contract_id:
                contract.update(updates)
                contract["updated_at"] = now_iso()
                self._write(data)
                return contract
        raise KeyError(contract_id)

    def append_event(self, contract_id: str, event: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        for contract in data["contracts"]:
            if contract["id"] == contract_id:
                event = {"time": now_iso(), **event}
                contract.setdefault("review", {}).setdefault("events", []).append(event)
                contract["updated_at"] = now_iso()
                self._write(data)
                return event
        raise KeyError(contract_id)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

