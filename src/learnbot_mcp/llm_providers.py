"""Unified local + cloud LLM provider registry, keystore, and chat proxy helpers.

Fleet pattern per arxiv-mcp/docs/SPEC-llm-providers.md: the webapp never talks
to vendors from the browser. All traffic goes through the backend, and API keys
live in a 0600 keystore under the data dir (or env vars, which win).

Provider IDs and key env names intentionally match the local-llm-mcp gateway
so a later "delegate to gateway when reachable" step is a drop-in.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import suppress
from pathlib import Path
from typing import Any

import httpx

log = logging.getLogger(__name__)

LOCAL_PROBE_TIMEOUT = 3.0
CLOUD_TIMEOUT = 30.0
CHAT_TIMEOUT = 120.0
KEYSTORE_NAME = "llm_keys.json"
ANTHROPIC_VERSION = "2023-06-01"
OLLAMA_NUM_CTX = 32768

PROVIDERS: tuple[dict[str, Any], ...] = (
    {
        "id": "ollama",
        "label": "Ollama",
        "kind": "local",
        "base_url": "http://127.0.0.1:11434",
        "chat_path": "/api/chat",
        "models_path": "/api/tags",
        "tag_style": "ollama",
        "key_env": None,
        "curated": [],
    },
    {
        "id": "lmstudio",
        "label": "LM Studio",
        "kind": "local",
        "base_url": "http://127.0.0.1:1234",
        "chat_path": "/v1/chat/completions",
        "models_path": "/v1/models",
        "tag_style": "openai",
        "key_env": None,
        "curated": [],
    },
    {
        "id": "vllm",
        "label": "vLLM",
        "kind": "local",
        "base_url": "http://127.0.0.1:8000",
        "chat_path": "/v1/chat/completions",
        "models_path": "/v1/models",
        "tag_style": "openai",
        "key_env": None,
        "curated": [],
    },
    {
        "id": "openai",
        "label": "OpenAI",
        "kind": "cloud",
        "base_url": "https://api.openai.com/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "OPENAI_API_KEY",
        "curated": ["gpt-4o", "gpt-4o-mini"],
    },
    {
        "id": "anthropic",
        "label": "Anthropic",
        "kind": "cloud",
        "base_url": "https://api.anthropic.com",
        "chat_path": "/v1/messages",
        "models_path": "/v1/models",
        "tag_style": "anthropic",
        "key_env": "ANTHROPIC_API_KEY",
        "curated": ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-fable-5.1"],
    },
    {
        "id": "deepseek",
        "label": "DeepSeek",
        "kind": "cloud",
        "base_url": "https://api.deepseek.com",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "DEEPSEEK_API_KEY",
        "curated": ["deepseek-v4-flash", "deepseek-v4-pro"],
    },
    {
        "id": "openrouter",
        "label": "OpenRouter",
        "kind": "cloud",
        "base_url": "https://openrouter.ai/api/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "OPENROUTER_API_KEY",
        "curated": [
            "openrouter/auto",
            "anthropic/claude-sonnet-4",
            "openai/gpt-4o",
            "meta-llama/llama-4-maverick",
        ],
    },
    {
        "id": "meta",
        "label": "Meta",
        "kind": "cloud",
        "base_url": "https://api.meta.ai/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "MODEL_API_KEY",
        "curated": [
            "muse-spark-1.3-contributor",
            "muse-spark-1.3",
            "muse-spark-1.2-contributor",
            "muse-spark-1.2",
            "muse-spark-1.1",
        ],
    },
    {
        "id": "google",
        "label": "Google",
        "kind": "cloud",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "GEMINI_API_KEY",
        "key_env_fallbacks": ["GOOGLE_API_KEY"],
        "curated": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
    },
    {
        "id": "groq",
        "label": "Groq",
        "kind": "cloud",
        "base_url": "https://api.groq.com/openai/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "GROQ_API_KEY",
        "curated": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
    },
    {
        "id": "mistral",
        "label": "Mistral",
        "kind": "cloud",
        "base_url": "https://api.mistral.ai/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "MISTRAL_API_KEY",
        "curated": ["mistral-large-latest", "mistral-small-latest"],
    },
    {
        "id": "together",
        "label": "Together",
        "kind": "cloud",
        "base_url": "https://api.together.xyz/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "TOGETHER_API_KEY",
        "curated": [
            "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
        ],
    },
    {
        "id": "fireworks",
        "label": "Fireworks",
        "kind": "cloud",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "FIREWORKS_API_KEY",
        "curated": [
            "accounts/fireworks/models/llama-v3p3-70b-instruct",
            "accounts/fireworks/models/mixtral-8x7b-instruct",
        ],
    },
    {
        "id": "cohere",
        "label": "Cohere",
        "kind": "cloud",
        "base_url": "https://api.cohere.com/compatibility/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "COHERE_API_KEY",
        "key_env_fallbacks": ["CO_API_KEY"],
        "curated": ["command-r-plus", "command-r"],
    },
    {
        "id": "xai",
        "label": "xAI",
        "kind": "cloud",
        "base_url": "https://api.x.ai/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "XAI_API_KEY",
        "curated": ["grok-3", "grok-3-mini", "grok-2-1212"],
    },
    {
        "id": "perplexity",
        "label": "Perplexity",
        "kind": "cloud",
        "base_url": "https://api.perplexity.ai",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "PERPLEXITY_API_KEY",
        "curated": ["sonar-pro", "sonar"],
    },
)


def get_provider(provider_id: str) -> dict[str, Any] | None:
    """Return the registry row for a provider ID, or None."""
    for row in PROVIDERS:
        if row["id"] == provider_id:
            return row
    return None


def require_provider(provider_id: str) -> dict[str, Any]:
    row = get_provider(provider_id)
    if row is None:
        known = ", ".join(r["id"] for r in PROVIDERS)
        raise ValueError(f"Unknown provider '{provider_id}'. Known: {known}")
    return row


def keystore_path() -> Path:
    from learnbot_mcp.config import get_settings

    db_path = Path(get_settings().db_path or "data/chatbot.db")
    parent = db_path.parent if str(db_path.parent) not in ("", ".") else Path("data")
    parent.mkdir(parents=True, exist_ok=True)
    return parent / KEYSTORE_NAME


def _read_keystore() -> dict[str, str]:
    path = keystore_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("llm keystore unreadable (%s); treating as empty", exc)
        return {}
    return {k: v for k, v in data.items() if isinstance(v, str) and v}


def _write_keystore(entries: dict[str, str]) -> None:
    path = keystore_path()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        log.debug("chmod 0600 on keystore failed (non-POSIX fs); continuing")
    os.replace(tmp, path)
    with suppress(OSError):
        os.chmod(path, 0o600)


def get_key(provider_id: str) -> str:
    """Resolve an API key: env var(s) first, then keystore. Empty when unset."""
    row = require_provider(provider_id)
    env_names = [row.get("key_env"), *(row.get("key_env_fallbacks") or [])]
    for env_name in env_names:
        if not env_name:
            continue
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    return _read_keystore().get(provider_id, "")


def is_configured(provider_id: str) -> bool:
    """True when a cloud provider has a key available. Locals need no key."""
    row = require_provider(provider_id)
    if row["kind"] == "local":
        return True
    return bool(get_key(provider_id))


def save_key(provider_id: str, api_key: str) -> None:
    row = require_provider(provider_id)
    if row["kind"] != "cloud":
        raise ValueError(f"Provider '{provider_id}' takes no API key")
    key = (api_key or "").strip()
    if not key:
        raise ValueError("Empty API key")
    entries = _read_keystore()
    entries[provider_id] = key
    _write_keystore(entries)


def delete_key(provider_id: str) -> bool:
    require_provider(provider_id)
    entries = _read_keystore()
    if provider_id not in entries:
        return False
    del entries[provider_id]
    _write_keystore(entries)
    return True


def public_provider_info() -> list[dict[str, Any]]:
    """Registry rows safe for GET responses: capability flags, never key bytes."""
    return [
        {
            "id": r["id"],
            "label": r["label"],
            "kind": r["kind"],
            "base_url": r["base_url"],
            "needs_key": r["kind"] == "cloud",
            "key_env": r.get("key_env"),
            "configured": is_configured(r["id"]),
        }
        for r in PROVIDERS
    ]


def _parse_model_list(tag_style: str, payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    if tag_style == "ollama":
        models = payload.get("models") or []
        return [m.get("name", "") for m in models if isinstance(m, dict) and m.get("name")]
    if tag_style == "anthropic":
        data = payload.get("data") or []
        return [m.get("id", "") for m in data if isinstance(m, dict) and m.get("id")]
    data = payload.get("data") or []
    return [m.get("id", "") for m in data if isinstance(m, dict) and m.get("id")]


async def probe_local(provider_id: str) -> tuple[bool, list[str]]:
    """Probe a local engine (fast timeout). Returns (reachable, models)."""
    row = require_provider(provider_id)
    if row["kind"] != "local":
        raise ValueError(f"Provider '{provider_id}' is not local")
    url = row["base_url"] + row["models_path"]
    try:
        async with httpx.AsyncClient(timeout=LOCAL_PROBE_TIMEOUT) as client:
            resp = await client.get(url)
    except Exception as exc:
        log.debug("local probe %s failed: %s", provider_id, exc)
        return False, []
    if resp.status_code >= 500:
        return False, []
    try:
        models = _parse_model_list(row["tag_style"], resp.json())
    except Exception:
        models = []
    return True, models


async def list_models(provider_id: str, api_key: str = "") -> dict[str, Any]:
    """Model list with source flag. Cloud: live when keyed, else curated.

    api_key overrides the stored/env key for this call only (lets Test
    validate a typed-but-unsaved key). Unkeyed clouds return curated names
    with key_missing=True -- callers must not report those as success.
    """
    row = require_provider(provider_id)
    if row["kind"] == "local":
        reachable, models = await probe_local(provider_id)
        return {
            "provider": provider_id,
            "models": models,
            "source": "live" if reachable else "none",
        }
    key = (api_key or "").strip() or get_key(provider_id)
    if not key:
        return {
            "provider": provider_id,
            "models": list(row["curated"]),
            "source": "curated",
            "key_missing": True,
            "note": "Save a key for the live list. Curated names still work once keyed.",
        }
    url = row["base_url"] + row["models_path"]
    headers = _auth_headers(row, key)
    try:
        async with httpx.AsyncClient(timeout=CLOUD_TIMEOUT) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            models = _parse_model_list(row["tag_style"], resp.json())
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        log.warning("live model list for %s HTTP %s; curated fallback", provider_id, status)
        if status in (401, 403):
            error = f"{row['label']} rejected the key (HTTP {status}) -- check the key, then Save and Test again."
        else:
            error = f"{row['label']} HTTP {status}."
        return {
            "provider": provider_id,
            "models": list(row["curated"]),
            "source": "curated",
            "error": error,
        }
    except Exception as exc:
        log.warning("live model list for %s failed (%s); curated fallback", provider_id, exc)
        return {"provider": provider_id, "models": list(row["curated"]), "source": "curated"}
    if not models:
        return {"provider": provider_id, "models": list(row["curated"]), "source": "curated"}
    return {"provider": provider_id, "models": models, "source": "live"}


def _auth_headers(row: dict[str, Any], api_key: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if row["id"] == "anthropic":
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = ANTHROPIC_VERSION
    elif row["id"] == "openrouter":
        headers["Authorization"] = f"Bearer {api_key}"
        headers["HTTP-Referer"] = "http://127.0.0.1:11102/"
        headers["X-Title"] = "learnbot-mcp"
    elif row["kind"] == "cloud":
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _openai_body(model: str, messages: list[dict[str, Any]]) -> dict[str, Any]:
    return {"model": model, "messages": messages, "stream": False}


def _to_anthropic(model: str, messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Map OpenAI messages array to the Anthropic Messages API body."""
    system_parts: list[str] = []
    converted: list[dict[str, Any]] = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            system_parts.append(str(content))
        elif role in ("user", "assistant"):
            converted.append({"role": role, "content": str(content)})
        else:
            converted.append({"role": "user", "content": str(content)})
    body: dict[str, Any] = {"model": model, "max_tokens": 1024, "messages": converted}
    if system_parts:
        body["system"] = "\n\n".join(system_parts)
    return body


def _from_anthropic(payload: dict[str, Any]) -> str:
    blocks = payload.get("content") or []
    texts = [b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
    return "".join(texts)


def _to_ollama_native(model: str, messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Ollama native /api/chat: honors options.num_ctx (its /v1 ignores options)."""
    converted = [
        {"role": m.get("role", "user"), "content": str(m.get("content", ""))} for m in messages
    ]
    return {
        "model": model,
        "messages": converted,
        "stream": False,
        "options": {"num_ctx": OLLAMA_NUM_CTX},
    }


def _from_ollama_native(payload: dict[str, Any]) -> str:
    return str((payload.get("message") or {}).get("content", ""))


def _ollama_stream_text(payload: dict[str, Any]) -> str:
    if payload.get("done"):
        return ""
    return str((payload.get("message") or {}).get("content", ""))


async def chat_complete(
    provider_id: str,
    model: str,
    messages: list[dict[str, Any]],
) -> str:
    """Non-streaming chat via the backend proxy. Returns assistant text."""
    row = require_provider(provider_id)
    if not model.strip():
        raise ValueError("Empty model name")
    key = get_key(provider_id) if row["kind"] == "cloud" else ""
    if row["kind"] == "cloud" and not key:
        raise ValueError(f"Provider '{provider_id}' has no API key configured")
    headers = _auth_headers(row, key)
    if row["id"] == "anthropic":
        url = row["base_url"] + row["chat_path"]
        body = _to_anthropic(model, messages)
    elif row["id"] == "ollama":
        url = row["base_url"] + row["chat_path"]
        body = _to_ollama_native(model, messages)
    else:
        url = row["base_url"] + row["chat_path"]
        body = _openai_body(model, messages)
    try:
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        raise RuntimeError(f"Provider '{provider_id}' HTTP {status}") from exc
    except Exception as exc:
        raise RuntimeError(f"Provider '{provider_id}' unreachable ({exc})") from exc
    if row["id"] == "anthropic":
        return _from_anthropic(data)
    if row["id"] == "ollama":
        return _from_ollama_native(data)
    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Provider '{provider_id}' returned an unexpected body") from exc


def _openai_sse_chunk(model: str, text: str) -> bytes:
    chunk = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}],
    }
    return ("data: " + json.dumps(chunk) + "\n\n").encode("utf-8")


async def chat_stream(
    provider_id: str,
    model: str,
    messages: list[dict[str, Any]],
) -> AsyncIterator[bytes]:
    """Streaming chat as OpenAI-style SSE bytes, normalized for every provider."""
    row = require_provider(provider_id)
    if not model.strip():
        raise ValueError("Empty model name")
    key = get_key(provider_id) if row["kind"] == "cloud" else ""
    if row["kind"] == "cloud" and not key:
        raise ValueError(f"Provider '{provider_id}' has no API key configured")
    headers = _auth_headers(row, key)
    headers["Accept"] = "text/event-stream"
    url = row["base_url"] + row["chat_path"]
    if row["id"] == "anthropic":
        body = _to_anthropic(model, messages)
    elif row["id"] == "ollama":
        body = _to_ollama_native(model, messages)
    else:
        body = _openai_body(model, messages)
    body["stream"] = True
    async with (
        httpx.AsyncClient(timeout=CHAT_TIMEOUT) as client,
        client.stream("POST", url, json=body, headers=headers) as resp,
    ):
        if row["id"] == "anthropic":
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line[6:].strip()
                if payload in ("[DONE]", ""):
                    continue
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                if event.get("type") == "content_block_delta":
                    text = (event.get("delta") or {}).get("text", "")
                    if text:
                        yield _openai_sse_chunk(model, text)
        elif row["id"] == "ollama":
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                text = _ollama_stream_text(event)
                if text:
                    yield _openai_sse_chunk(model, text)
        else:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    yield (line + "\n\n").encode("utf-8")
    yield b"data: [DONE]\n\n"
