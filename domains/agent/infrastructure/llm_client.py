"""LLM client — calls AI providers using API keys from auth domain."""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict = field(default_factory=dict)


class LLMClient:
    """Calls AI providers using API keys from auth domain (or env fallback)."""

    def __init__(self, auth_base_url: str = "http://auth:8070") -> None:
        self._auth_url = auth_base_url

    # ------------------------------------------------------------------
    # Key resolution
    # ------------------------------------------------------------------

    async def _get_api_key(self, provider: str) -> str | None:
        """Fetch API key from auth domain's connection store, fall back to env."""
        # Try auth domain first
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._auth_url}/api/v1/auth/key/{provider}")
                if resp.status_code == 200:
                    data = resp.json()
                    key = data.get("api_key")
                    if key:
                        return key
        except Exception:
            logger.debug("Auth domain unreachable, falling back to env var for %s", provider)

        # Fallback: environment variables (useful for dev / docker-compose)
        env_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
        }
        env_var = env_map.get(provider)
        if env_var:
            return os.getenv(env_var) or None
        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def chat(
        self,
        provider: str,
        model: str,
        system_prompt: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a chat request to the specified provider."""
        api_key = await self._get_api_key(provider)
        if not api_key:
            raise ValueError(f"No API key configured for {provider}")

        if provider == "anthropic":
            return await self._call_anthropic(api_key, model, system_prompt, messages, temperature, max_tokens)
        elif provider == "openai":
            return await self._call_openai(api_key, model, system_prompt, messages, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    # ------------------------------------------------------------------
    # Provider implementations
    # ------------------------------------------------------------------

    async def _call_anthropic(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "system": system_prompt,
                    "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return LLMResponse(
                content=data["content"][0]["text"],
                model=data["model"],
                usage=data.get("usage", {}),
            )

    async def _call_openai(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        msgs = [{"role": "system", "content": system_prompt}]
        msgs.extend({"role": m["role"], "content": m["content"]} for m in messages)
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": msgs,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=data["model"],
                usage=data.get("usage", {}),
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def extract_json_array(text: str) -> list[dict] | None:
        """Extract a JSON array from LLM output that may contain markdown fences."""
        # Strip markdown code fences
        cleaned = re.sub(r"```(?:json)?\s*", "", text)
        cleaned = re.sub(r"```", "", cleaned)
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None
