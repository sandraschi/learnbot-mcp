"""LLM client - delegates to local-llm-mcp or talks directly to Ollama."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from learnbot_mcp.config import get_settings

log = logging.getLogger(__name__)

_DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
_DEFAULT_MODEL = "llama3.2:3b"


async def chat_completion(
    messages: list[dict[str, str]],
    system_prompt: str = "",
    model: str = "",
    stream: bool = False,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Call an LLM with message history.

    Tries local-llm-mcp first. Falls back to direct Ollama call.
    Default model is qwen3.5-9b-deepseek-v4-flash.

    Returns {"response": str, "model": str, "provider": str}.
    """
    cfg = get_settings()
    model_name = model or cfg.llm_model or _DEFAULT_MODEL
    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt[:4000]})
    full_messages.extend(messages)

    # Try 1: local-llm-mcp
    try:
        base = cfg.llm_base_url.rstrip("/")
        result = await _call_local_llm(base, full_messages, model_name, stream, timeout)
        if result:
            return result
    except Exception as e:
        log.info("local-llm-mcp unreachable (%s), trying Ollama", e)

    # Try 2: Ollama directly
    try:
        result = await _call_ollama(full_messages, model_name, stream, timeout)
        if result:
            return result
    except Exception as e:
        log.warning("Ollama also unreachable: %s", e)

    raise RuntimeError("No LLM available (tried local-lll-mcp and Ollama)")


async def _call_local_llm(
    base: str, messages: list[dict], model: str, stream: bool, timeout: float
) -> dict | None:
    """Call local-llm-mcp's /api/llm/chat endpoint."""
    url = f"{base}/api/llm/chat"
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        resp = await client.post(url, json={"messages": messages, "model": model, "stream": stream})
        if resp.status_code != 200:
            return None
        data = resp.json()
    text = _extract_response(data)
    if text:
        return {"response": text, "model": data.get("model", model), "provider": "local-llm-mcp"}
    return None


async def _call_ollama(
    messages: list[dict], model: str, stream: bool, timeout: float
) -> dict | None:
    """Call Ollama's OpenAI-compatible /v1/chat/completions endpoint."""
    url = f"{_DEFAULT_OLLAMA_URL}/v1/chat/completions"
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        resp = await client.post(url, json={"messages": messages, "model": model, "stream": stream})
        if resp.status_code != 200:
            return None
        data = resp.json()
    text = _extract_response(data)
    if text:
        return {"response": text, "model": data.get("model", model), "provider": "ollama"}
    return None


def _extract_response(data: dict) -> str:
    """Extract response text from various API response shapes."""
    return (
        data.get("response")
        or data.get("content")
        or data.get("message", {}).get("content")
        or (data.get("choices") and data["choices"][0].get("message", {}).get("content"))
        or ""
    )


def build_history(turns: list, max_turns: int = 20) -> list[dict[str, str]]:
    """Convert DB turns (dicts or Row objects) to message history for the LLM call."""
    messages = []
    for t in turns[-max_turns:]:
        try:
            role = t["role"] if isinstance(t, dict) else t["role"]
        except (KeyError, TypeError):
            continue
        if role not in ("user", "assistant"):
            continue
        content_raw = t.get("content", "") if isinstance(t, dict) else (t["content"] or "")
        content = str(content_raw)[:2000]
        messages.append({"role": role, "content": content})
    return messages
