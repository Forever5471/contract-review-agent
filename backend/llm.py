from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

from .storage import ROOT_DIR


def load_local_env() -> None:
    for path in [ROOT_DIR / ".env.local", ROOT_DIR / ".env"]:
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    api_key: str
    model: str
    base_url: str
    temperature: float
    max_tokens: int
    timeout_seconds: int
    thinking: str

    @classmethod
    def from_env(cls) -> "LLMConfig | None":
        load_local_env()
        provider = os.getenv("LLM_PROVIDER", "").strip().lower()
        api_key = os.getenv("GLM_API_KEY", "").strip()
        if not provider and api_key:
            provider = "glm"
        if provider != "glm" or not api_key:
            return None
        return cls(
            provider="glm",
            api_key=api_key,
            model=os.getenv("GLM_MODEL", "glm-5").strip() or "glm-5",
            base_url=os.getenv("GLM_BASE_URL", "https://api.z.ai/api/paas/v4").strip(),
            temperature=float(os.getenv("GLM_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("GLM_MAX_TOKENS", "900")),
            timeout_seconds=int(os.getenv("GLM_TIMEOUT_SECONDS", "30")),
            thinking=os.getenv("GLM_THINKING", "disabled").strip() or "disabled",
        )

    @classmethod
    def from_agent_model(cls, model: dict[str, Any] | None) -> "LLMConfig | None":
        model = model or {}
        provider = str(model.get("provider") or "").strip().lower()
        api_key = str(model.get("api_key") or "").strip()
        enabled = bool(model.get("enabled", False))
        if not enabled or provider != "glm" or not api_key:
            return None
        return cls(
            provider="glm",
            api_key=api_key,
            model=str(model.get("model") or "glm-5").strip() or "glm-5",
            base_url=str(model.get("base_url") or os.getenv("GLM_BASE_URL", "https://api.z.ai/api/paas/v4")).strip(),
            temperature=float(model.get("temperature", 0.1)),
            max_tokens=int(model.get("max_tokens", os.getenv("GLM_MAX_TOKENS", "900"))),
            timeout_seconds=int(model.get("timeout_seconds", os.getenv("GLM_TIMEOUT_SECONDS", "30"))),
            thinking=str(model.get("thinking") or os.getenv("GLM_THINKING", "disabled")).strip() or "disabled",
        )

    @property
    def endpoint(self) -> str:
        url = self.base_url.rstrip("/")
        if url.endswith("/chat/completions"):
            return url
        return f"{url}/chat/completions"

    def public_status(self) -> dict[str, Any]:
        return {
            "configured": True,
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "thinking": self.thinking,
            "api_key_set": bool(self.api_key),
        }


class GLMChatClient:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    @property
    def model(self) -> str:
        return self.config.model

    def complete_json(self, messages: list[dict[str, str]], request_id: str | None = None) -> dict[str, Any]:
        request_id = request_id or f"rule-{uuid.uuid4().hex[:20]}"
        body = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "response_format": {"type": "json_object"},
            "thinking": {"type": self.config.thinking, "clear_thinking": True},
            "request_id": request_id[:64],
        }
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        http_request = request.Request(
            self.config.endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=self.config.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            return {"ok": False, "error": f"GLM HTTP {exc.code}", "provider": "glm", "model": self.model}
        except Exception as exc:
            return {"ok": False, "error": f"GLM 调用失败：{exc}", "provider": "glm", "model": self.model}

        message = ((data.get("choices") or [{}])[0].get("message") or {})
        content = message.get("content") or ""
        parsed = _parse_json_content(content)
        if parsed is None:
            return {
                "ok": False,
                "error": "GLM 返回内容不是有效 JSON。",
                "provider": "glm",
                "model": self.model,
                "request_id": data.get("request_id", request_id),
            }
        return {
            "ok": True,
            "provider": "glm",
            "model": self.model,
            "request_id": data.get("request_id", request_id),
            "json": parsed,
            "usage": data.get("usage", {}),
        }


def build_llm_client(model: dict[str, Any] | None = None) -> GLMChatClient | None:
    config = LLMConfig.from_agent_model(model) if model else LLMConfig.from_env()
    if config is None:
        return None
    return GLMChatClient(config)


def get_llm_status() -> dict[str, Any]:
    config = LLMConfig.from_env()
    if config is None:
        return {"configured": False, "provider": None, "model": None, "api_key_set": False}
    return config.public_status()


def _parse_json_content(content: str) -> dict[str, Any] | None:
    content = content.strip()
    if not content:
        return None
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.S)
    if fenced:
        try:
            parsed = json.loads(fenced.group(1))
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            pass
    start = content.find("{")
    end = content.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(content[start : end + 1])
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    return None
