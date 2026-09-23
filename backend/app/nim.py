"""Observable multi-provider LLM gateway.

NVIDIA NIM remains the preferred provider for the SIH deployment. OpenRouter,
Groq, and Gemini can be configured as fallbacks. Domain decisions never depend
on an LLM: callers always supply deterministic fallback text.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

import httpx

from app.config import settings


@dataclass
class GenerationResult:
    text: str
    provider: str
    model: str
    mode: str
    attempts: list[dict[str, Any]] = field(default_factory=list)

    def metadata(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("text", None)
        return data


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    name: str
    base_url: str
    model: str
    api_key: str | None
    protocol: str

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model)


class LLMGateway:
    def __init__(self) -> None:
        self.last_generation: dict[str, Any] | None = None

    def _providers(self) -> dict[str, ProviderSpec]:
        return {
            "nvidia": ProviderSpec("nvidia", "NVIDIA NIM", settings.nim_base_url.rstrip("/"), settings.nim_model, settings.nim_api_key, "openai"),
            "openrouter": ProviderSpec("openrouter", "OpenRouter", settings.openrouter_base_url.rstrip("/"), settings.openrouter_model, settings.openrouter_api_key, "openai"),
            "groq": ProviderSpec("groq", "Groq", settings.groq_base_url.rstrip("/"), settings.groq_model, settings.groq_api_key, "openai"),
            "gemini": ProviderSpec("gemini", "Google Gemini", settings.gemini_base_url.rstrip("/"), settings.gemini_model, settings.gemini_api_key, "gemini"),
        }

    @property
    def configured(self) -> bool:
        return any(provider.configured for provider in self._providers().values())

    @property
    def model(self) -> str:
        providers = self._providers()
        for provider_id in settings.llm_provider_order:
            if providers[provider_id].configured:
                return providers[provider_id].model
        return settings.nim_model

    def status(self) -> dict[str, Any]:
        providers = self._providers()
        rows = [
            {
                "id": provider.id,
                "name": provider.name,
                "configured": provider.configured,
                "model": provider.model,
                "base_url": provider.base_url,
                "protocol": provider.protocol,
            }
            for provider in providers.values()
        ]
        configured_order = [provider_id for provider_id in settings.llm_provider_order if providers[provider_id].configured]
        return {
            "provider": "Multi-provider LLM gateway",
            "configured": bool(configured_order),
            "mode": "LIVE_READY" if configured_order else "DETERMINISTIC_FALLBACK",
            "priority": settings.llm_provider_order,
            "preferred_provider": configured_order[0] if configured_order else None,
            "model": providers[configured_order[0]].model if configured_order else settings.nim_model,
            "providers": rows,
            "last_generation": self.last_generation,
        }

    def models(self) -> list[dict[str, Any]]:
        return [
            {"provider": row["id"], "id": row["model"], "configured": row["configured"]}
            for row in self.status()["providers"]
        ]

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        if isinstance(exc, httpx.HTTPStatusError):
            return f"HTTP_{exc.response.status_code}"
        if isinstance(exc, httpx.TimeoutException):
            return "TIMEOUT"
        if isinstance(exc, httpx.ConnectError):
            return "CONNECTION_ERROR"
        return type(exc).__name__.upper()

    def _openai_chat(self, provider: ProviderSpec, system: str, user: str) -> tuple[str, str]:
        payload = {
            "model": provider.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {provider.api_key}", "Content-Type": "application/json"}
        if provider.id == "openrouter":
            headers.update({"HTTP-Referer": "https://stuskilllink.local", "X-OpenRouter-Title": "StuSkillLink"})
        with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
            response = client.post(f"{provider.base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        text = str(data["choices"][0]["message"].get("content") or "").strip()
        if not text:
            raise ValueError("empty model response")
        return text, str(data.get("model") or provider.model)

    def _gemini_chat(self, provider: ProviderSpec, system: str, user: str) -> tuple[str, str]:
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "temperature": settings.llm_temperature,
                "maxOutputTokens": settings.llm_max_tokens,
            },
        }
        headers = {"x-goog-api-key": str(provider.api_key), "Content-Type": "application/json"}
        with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
            response = client.post(f"{provider.base_url}/models/{provider.model}:generateContent", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(str(part.get("text") or "") for part in parts).strip()
        if not text:
            raise ValueError("empty model response")
        return text, provider.model

    def generate(self, system: str, user: str, *, fallback: str, purpose: str = "general", preferred_provider: str | None = None) -> GenerationResult:
        providers = self._providers()
        attempts: list[dict[str, Any]] = []
        provider_order = list(settings.llm_provider_order)
        if preferred_provider in provider_order:
            provider_order.remove(preferred_provider)
            provider_order.insert(0, preferred_provider)
        for provider_id in provider_order:
            provider = providers[provider_id]
            if not provider.configured:
                attempts.append({"provider": provider.id, "status": "SKIPPED", "error": "NOT_CONFIGURED"})
                continue
            try:
                if provider.protocol == "gemini":
                    text, actual_model = self._gemini_chat(provider, system, user)
                else:
                    text, actual_model = self._openai_chat(provider, system, user)
                attempts.append({"provider": provider.id, "status": "SUCCESS"})
                result = GenerationResult(text, provider.id, actual_model, "LIVE", attempts)
                self.last_generation = {"purpose": purpose, **result.metadata()}
                return result
            except Exception as exc:
                attempts.append({"provider": provider.id, "status": "FAILED", "error": self._safe_error(exc)})
        result = GenerationResult(fallback, "deterministic", "rules", "FALLBACK", attempts)
        self.last_generation = {"purpose": purpose, **result.metadata()}
        return result

    def chat(self, system: str, user: str, *, fallback: str) -> str:
        return self.generate(system, user, fallback=fallback).text

    def structured_json(self, system: str, user: str, *, fallback: dict[str, Any]) -> dict[str, Any]:
        result = self.generate(system + " Return JSON only.", user, fallback=json.dumps(fallback), purpose="structured_json")
        try:
            text = result.text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else fallback
        except (TypeError, ValueError, json.JSONDecodeError):
            return fallback

    def embeddings(self, texts: list[str]) -> list[list[float]]:
        if not (settings.nim_api_key and settings.nim_embedding_model and texts):
            return []
        headers = {"Authorization": f"Bearer {settings.nim_api_key}", "Content-Type": "application/json"}
        payload = {"model": settings.nim_embedding_model, "input": texts, "input_type": "query"}
        try:
            with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
                response = client.post(f"{settings.nim_base_url.rstrip('/')}/embeddings", headers=headers, json=payload)
                response.raise_for_status()
                return [row.get("embedding", []) for row in response.json().get("data", [])]
        except Exception:
            return []


llm_gateway = LLMGateway()
# Backwards-compatible import name used by the existing routes/services.
nim_client = llm_gateway
