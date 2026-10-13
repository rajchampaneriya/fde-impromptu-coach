"""Tiny helper around Ollama's /api/chat and /api/embed (given on day 6).

On day 1 you wrote the raw HTTP call yourself. This file is the same call plus
three things every evaluation needs:

* a disk cache, so re-running a notebook costs nothing and gives the same answers;
* timing and token counts on every call;
* `run=` to ask the same question several times on purpose (to measure randomness).

It talks only to the Ollama server on your own Mac: free, private, no API key.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "qwen3:4b"          # Mac with 8 GB of memory? use "llama3.2:3b"
EMBED_MODEL = "embeddinggemma"
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"

_memory: Dict[str, Dict[str, Any]] = {}


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


def chat(messages: List[Dict[str, Any]], *, model: str = CHAT_MODEL, temperature: float = 0.0,
         seed: Optional[int] = None, tools: Optional[List[Dict]] = None, schema: Optional[Dict] = None,
         think: Optional[bool] = None, run: int = 0, use_cache: bool = True) -> Dict[str, Any]:
    """One chat call. Returns a dict with:
    content, tool_calls, message (the raw assistant message), tokens_in, tokens_out,
    seconds (of the original call, even when cached) and cached (True/False)."""
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
