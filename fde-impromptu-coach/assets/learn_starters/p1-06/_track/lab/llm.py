"""Tiny helper around Ollama's /api/chat and /api/embed (given on day 6).

On day 1 you wrote the raw HTTP call yourself. This file is the same call plus
three things every evaluation needs:

* a disk cache, so re-running a notebook costs nothing and gives the same answers;
* timing and token counts on every call;
* `run=` to ask the same question several times on purpose (to measure randomness).

It talks to the Ollama server on your own Mac: free, private, no API key.

Only the final run in project 6 uses a stronger model, switched with one line:

    llm.use("qwen3:14b")        # a bigger model in your own Ollama (free)
    llm.use("api:<model>")      # a paid model behind any OpenAI-compatible API, configured in .env:
                                #   LLM_BASE_URL=https://…/v1   LLM_API_KEY=…   (set a hard spending cap first)
    llm.use(llm.CHAT_MODEL)     # back to the small model

The API path speaks the same messages as Ollama (tool calls included), so your version B and agent loop run
unchanged. API_CALL_LIMIT stops a runaway loop long before your provider's cap does.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "qwen3:4b"          # Mac with 8 GB of memory? use "llama3.2:3b"
EMBED_MODEL = "embeddinggemma"
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"     # git-ignored: never commit a key
API_PREFIX = "api:"
API_CALL_LIMIT = int(os.environ.get("LLM_MAX_CALLS", "500"))  # API requests per Python session

_memory: Dict[str, Dict[str, Any]] = {}
_current = {"model": CHAT_MODEL}
_api_usage = {"calls": 0, "tokens_in": 0, "tokens_out": 0}


def use(model: str) -> str:
    """Switch the model every later chat() call uses (unless a call passes model=...)."""
    _current["model"] = model
    return model


def current_model() -> str:
    return _current["model"]


def api_usage() -> Dict[str, int]:
    """API requests and tokens sent in this Python session (cached answers are free and not counted)."""
    return dict(_api_usage)


def _env(name: str) -> str:
    """A setting from the environment, else from the .env file in your fde-first-principles folder."""
    if os.environ.get(name):
        return os.environ[name]
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.strip().removeprefix("export ").partition("=")
            if sep and key.strip() == name:
                return value.strip().strip('"').strip("'")
    return ""


def _cache_file(kind: str) -> Path:
    return CACHE_DIR / f"{kind}.jsonl"


def _load(kind: str) -> Dict[str, Any]:
    if kind not in _memory:
        _memory[kind] = {}
        path = _cache_file(kind)
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    item = json.loads(line)
                    _memory[kind][item["key"]] = item["value"]
    return _memory[kind]


def _store(kind: str, key: str, value: Any) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _load(kind)[key] = value
    with _cache_file(kind).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"key": key, "value": value}, ensure_ascii=False) + "\n")


def _key(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def chat(messages: List[Dict[str, Any]], *, model: Optional[str] = None, temperature: float = 0.0,
         seed: Optional[int] = None, tools: Optional[List[Dict]] = None, schema: Optional[Dict] = None,
         think: Optional[bool] = None, run: int = 0, use_cache: bool = True) -> Dict[str, Any]:
    """One chat call. Returns a dict with:
    content, tool_calls, message (the raw assistant message), tokens_in, tokens_out,
    seconds (of the original call, even when cached) and cached (True/False)."""
    model = model or _current["model"]
    if model.startswith(API_PREFIX):
        return _chat_api(messages, model=model, temperature=temperature, seed=seed, tools=tools, schema=schema,
                         run=run, use_cache=use_cache)
    body: Dict[str, Any] = {"model": model, "messages": messages, "stream": False,
                            "options": {"temperature": temperature}}
    if seed is not None:
        body["options"]["seed"] = seed
    if tools:
        body["tools"] = tools
    if schema:
        body["format"] = schema
    if think is None and model.startswith("qwen3"):
        think = False                # qwen3 "thinks" first by default; we switch it off for speed
    if think is not None:
        body["think"] = think
    key = _key({"body": body, "run": run})
    if use_cache and key in _load("chat"):
        return dict(_load("chat")[key], cached=True)
    started = time.perf_counter()
    response = requests.post(f"{OLLAMA}/api/chat", json=body, timeout=600)
    response.raise_for_status()
    data = response.json()
    message = data.get("message") or {}
    result = {
        "content": message.get("content") or "",
        "tool_calls": message.get("tool_calls") or [],
        "message": message,
        "tokens_in": int(data.get("prompt_eval_count") or 0),
        "tokens_out": int(data.get("eval_count") or 0),
        "seconds": round(time.perf_counter() - started, 3),
        "model": model,
    }
    _store("chat", key, result)
    return dict(result, cached=False)


def _to_openai(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ollama-style messages -> OpenAI-style: tool calls get ids, tool results point back to them."""
    out: List[Dict[str, Any]] = []
    pending: List[tuple] = []
    for m in messages:
        role = m.get("role")
        if role == "assistant":
            calls = []
            for i, call in enumerate(m.get("tool_calls") or []):
                fn = call.get("function") or {}
                args = fn.get("arguments", {})
                calls.append({"id": call.get("id") or f"call_{len(out)}_{i}", "type": "function",
                              "function": {"name": fn.get("name"),
                                           "arguments": args if isinstance(args, str) else json.dumps(args, ensure_ascii=False)}})
            msg: Dict[str, Any] = {"role": "assistant", "content": m.get("content") or ""}
            if calls:
                msg["tool_calls"] = calls
                pending = [(c["id"], c["function"]["name"]) for c in calls]
            out.append(msg)
        elif role == "tool":
            call_id = m.get("tool_call_id")
            if not call_id and pending:
                name = m.get("tool_name") or m.get("name")
                match = next((p for p in pending if p[1] == name), pending[0])
                pending.remove(match)
                call_id = match[0]
            content = m.get("content")
            out.append({"role": "tool", "tool_call_id": call_id or "call_0",
                        "content": content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)})
        else:
            out.append({"role": role, "content": m.get("content") or ""})
    return out


def _post_api(url: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """POST with a retry on rate limits and server errors, and a fallback when JSON schemas are not supported."""
    headers = {"Authorization": f"Bearer {_env('LLM_API_KEY') or 'none'}"}
    for attempt in range(4):
        if _api_usage["calls"] >= API_CALL_LIMIT:
            raise RuntimeError(f"API call limit reached ({API_CALL_LIMIT} requests). If your estimate allows more, "
                               f"raise llm.API_CALL_LIMIT; if not, something is looping.")
        _api_usage["calls"] += 1
        response = requests.post(url, json=body, headers=headers, timeout=300)
        if response.status_code in (429, 500, 502, 503, 504) and attempt < 3:
            time.sleep(2 * (attempt + 1) ** 2)
            continue
        if response.status_code == 400 and "response_format" in body and attempt < 3:
            fmt = body["response_format"].get("type")
            body = dict(body, response_format={"type": "json_object"}) if fmt == "json_schema" else \
                {k: v for k, v in body.items() if k != "response_format"}
            continue
        if response.status_code >= 400:
            raise RuntimeError(f"{url} answered {response.status_code}: {response.text[:300]}")
        return response.json()
    raise RuntimeError(f"{url}: still failing after retries")


def _chat_api(messages: List[Dict[str, Any]], *, model: str, temperature: float, seed: Optional[int],
              tools: Optional[List[Dict]], schema: Optional[Dict], run: int, use_cache: bool) -> Dict[str, Any]:
    base = _env("LLM_BASE_URL").rstrip("/")
    if not base:
        raise RuntimeError("Set LLM_BASE_URL (and LLM_API_KEY) in .env in your fde-first-principles folder. "
                           "Free dry run: LLM_BASE_URL=http://localhost:11434/v1 (your own Ollama).")
    body: Dict[str, Any] = {"model": model[len(API_PREFIX):], "messages": _to_openai(messages),
                            "temperature": temperature}
    if seed is not None:
        body["seed"] = seed
    if tools:
        body["tools"] = tools
    if schema:
        body["response_format"] = {"type": "json_schema", "json_schema": {"name": "answer", "schema": schema}}
    key = _key({"api": base, "body": body, "run": run})
    if use_cache and key in _load("chat"):
        return dict(_load("chat")[key], cached=True)
    started = time.perf_counter()
    data = _post_api(f"{base}/chat/completions", body)
    reply = (data.get("choices") or [{}])[0].get("message") or {}
    calls = []
    for call in reply.get("tool_calls") or []:
        fn = call.get("function") or {}
        args = fn.get("arguments") or "{}"
        try:
            args = json.loads(args) if isinstance(args, str) else args
        except json.JSONDecodeError:
            args = {"_raw": args}
        calls.append({"id": call.get("id"), "function": {"name": fn.get("name"), "arguments": args}})
    message: Dict[str, Any] = {"role": "assistant", "content": reply.get("content") or ""}
    if calls:
        message["tool_calls"] = calls
    usage = data.get("usage") or {}
    result = {
        "content": message["content"],
        "tool_calls": calls,
        "message": message,
        "tokens_in": int(usage.get("prompt_tokens") or 0),
        "tokens_out": int(usage.get("completion_tokens") or 0),
        "seconds": round(time.perf_counter() - started, 3),
        "model": model,
    }
    _api_usage["tokens_in"] += result["tokens_in"]
    _api_usage["tokens_out"] += result["tokens_out"]
    _store("chat", key, result)
    return dict(result, cached=False)


def embed(texts: List[str], *, model: str = EMBED_MODEL, use_cache: bool = True) -> List[List[float]]:
    """One vector per text, from Ollama's /api/embed (cached per text)."""
    cache = _load("embed")
    keys = [_key({"model": model, "text": t}) for t in texts]
    missing = [t for t, k in zip(texts, keys) if not (use_cache and k in cache)]
    if missing:
        response = requests.post(f"{OLLAMA}/api/embed", json={"model": model, "input": missing}, timeout=600)
        response.raise_for_status()
        for text, vector in zip(missing, response.json()["embeddings"]):
            _store("embed", _key({"model": model, "text": text}), vector)
    return [cache[k] for k in keys]


def extract_json(text: str) -> Dict[str, Any]:
    """The first {...} object in a model's text (models sometimes add words or ``` fences).
    Raises ValueError if there is none."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    raise ValueError(f"No JSON object found in: {text[:200]!r}")
