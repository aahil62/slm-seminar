"""Model backends: Ollama (local SLMs), Groq (cloud LLMs) and a fake for tests."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional, Protocol

from . import config
from .config import ModelConfig


@dataclass
class Completion:
    text: str
    thinking: str
    prompt_tokens: int
    completion_tokens: int
    wall_s: float
    model_digest: Optional[str] = None


USER_AGENT = "slmcheck/0.1 (research harness; python urllib)"


class BackendError(RuntimeError):
    pass


class RateLimited(BackendError):
    def __init__(self, retry_after_s: float):
        super().__init__(f"rate limited; retry after {retry_after_s:.0f}s")
        self.retry_after_s = retry_after_s


class Backend(Protocol):
    def complete(self, messages: list[dict], temperature: float, top_p: float, seed: int,
                 max_tokens: int) -> Completion: ...


Opener = Callable[[urllib.request.Request, float], tuple[int, dict, bytes]]


def default_opener(req: urllib.request.Request, timeout: float) -> tuple[int, dict, bytes]:
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, e.read() or b""


def _post(opener: Opener, url: str, payload: dict, headers: dict, timeout: float):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    return opener(req, timeout)


class FakeBackend:
    def __init__(self, script: Callable[[list[dict], int], str]):
        self.script = script

    def complete(self, messages, temperature, top_p, seed, max_tokens):
        text = self.script(messages, seed)
        return Completion(text, "", sum(len(m["content"]) // 4 for m in messages),
                          max(1, len(text) // 4), 0.0, "fake")


class OllamaBackend:
    def __init__(self, cfg: ModelConfig, opener: Opener = default_opener,
                 base_url: str = config.OLLAMA_URL):
        self.cfg, self.opener, self.base = cfg, opener, base_url
        self.digest = self._digest()

    def _digest(self) -> Optional[str]:
        try:
            status, _, body = self.opener(urllib.request.Request(self.base + "/api/tags"), 10)
            for m in json.loads(body).get("models", []):
                if m.get("name") == self.cfg.model or m.get("model") == self.cfg.model:
                    return m.get("digest")
        except (OSError, ValueError):
            pass
        return None

    def complete(self, messages, temperature, top_p, seed, max_tokens):
        payload = {
            "model": self.cfg.model, "messages": messages, "stream": False, "keep_alive": "10m",
            "options": {"temperature": temperature, "top_p": top_p, "seed": seed,
                        "num_predict": max_tokens, "num_ctx": max_tokens + 4096},
        }
        if self.cfg.think is not None:
            payload["think"] = self.cfg.think
        t0 = time.time()
        status, _, body = _post(self.opener, self.base + "/api/chat", payload, {}, 1800)
        if status != 200:
            raise BackendError(f"ollama HTTP {status}: {body[:300]!r}")
        d = json.loads(body)
        msg = d.get("message", {})
        return Completion(msg.get("content", ""), msg.get("thinking", "") or "",
                          d.get("prompt_eval_count", 0), d.get("eval_count", 0),
                          time.time() - t0, self.digest)


class GroqBackend:
    """OpenAI-compatible chat completions; subclasses only change the endpoint and key variable."""
    URL, KEY_ENV, LABEL, MAX_TOKENS_FIELD = config.GROQ_URL, "GROQ_API_KEY", "groq", "max_completion_tokens"

    def __init__(self, cfg: ModelConfig, opener: Opener = default_opener):
        if not os.environ.get(self.KEY_ENV):
            raise BackendError(f"{self.KEY_ENV} is not set")
        self.cfg, self.opener = cfg, opener

    def __repr__(self):
        return f"{type(self).__name__}(model={self.cfg.model!r})"

    def complete(self, messages, temperature, top_p, seed, max_tokens):
        payload = {"model": self.cfg.model, "messages": messages, "temperature": temperature,
                   "top_p": top_p, "seed": seed, self.MAX_TOKENS_FIELD: max_tokens,
                   **self.cfg.extra}
        # Groq sits behind Cloudflare, which rejects urllib's default "Python-urllib/x.y" agent
        # with HTTP 403 "error code: 1010"; send an explicit client name instead.
        headers = {"Authorization": "Bearer " + os.environ[self.KEY_ENV], "User-Agent": USER_AGENT}
        t0 = time.time()
        for attempt in range(4):
            status, hdrs, body = _post(self.opener, self.URL, payload, headers, 600)
            if status == 429:
                raise RateLimited(float(hdrs.get("retry-after", 60) or 60))
            if status >= 500 and attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            break
        if status != 200:
            raise BackendError(f"{self.LABEL} HTTP {status}: {body[:300]!r}")
        d = json.loads(body)
        msg = d["choices"][0]["message"]
        usage = d.get("usage", {})
        return Completion(msg.get("content") or "", msg.get("reasoning") or "",
                          usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0),
                          time.time() - t0, self.cfg.model)


class DeepInfraBackend(GroqBackend):
    """Second cloud provider, used because Groq moved Llama-3.3-70B to Enterprise-only."""
    URL, KEY_ENV, LABEL, MAX_TOKENS_FIELD = config.DEEPINFRA_URL, "DEEPINFRA_API_KEY", "deepinfra", "max_tokens"


def make_backend(cfg: ModelConfig, opener: Opener = default_opener) -> Backend:
    if cfg.provider == "ollama":
        return OllamaBackend(cfg, opener)
    if cfg.provider == "groq":
        return GroqBackend(cfg, opener)
    if cfg.provider == "deepinfra":
        return DeepInfraBackend(cfg, opener)
    raise BackendError(f"no real backend for provider {cfg.provider!r}")
