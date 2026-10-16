import json

import pytest

from slmcheck import backends
from slmcheck.config import ModelConfig

MSG = [{"role": "user", "content": "hi"}]


class StubOpener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, req, timeout):
        self.requests.append(req)
        return self.responses.pop(0)


def test_fake_backend_returns_script_output():
    b = backends.FakeBackend(lambda messages, seed: f"seed={seed}")
    c = b.complete(MSG, temperature=0.0, top_p=1.0, seed=7, max_tokens=10)
    assert c.text == "seed=7" and c.completion_tokens > 0


def test_ollama_payload_shape():
    body = json.dumps({"message": {"content": "```python\nprint(1)\n```", "thinking": "hmm"},
                       "prompt_eval_count": 11, "eval_count": 22}).encode()
    tags = json.dumps({"models": [{"name": "qwen3:4b", "digest": "abc123"}]}).encode()
    op = StubOpener([(200, {}, tags), (200, {}, body)])
    cfg = ModelConfig("q", "ollama", "qwen3:4b", k=2, think=True, max_tokens=8192)
    c = backends.make_backend(cfg, opener=op).complete(MSG, 0.8, 0.95, 42, 8192)
    sent = json.loads(op.requests[-1].data)
    assert sent["think"] is True and sent["stream"] is False
    assert sent["options"]["seed"] == 42 and sent["options"]["num_predict"] == 8192
    assert sent["options"]["num_ctx"] >= 8192
    assert c.text.startswith("```python") and c.thinking == "hmm"
    assert (c.prompt_tokens, c.completion_tokens, c.model_digest) == (11, 22, "abc123")


def test_ollama_omits_think_when_unset():
    body = json.dumps({"message": {"content": "x"}, "prompt_eval_count": 1, "eval_count": 1}).encode()
    op = StubOpener([(200, {}, b'{"models": []}'), (200, {}, body)])
    cfg = ModelConfig("c", "ollama", "qwen2.5-coder:7b", k=5)
    backends.make_backend(cfg, opener=op).complete(MSG, 0.0, 1.0, 1, 100)
    assert "think" not in json.loads(op.requests[-1].data)


def test_groq_payload_and_parse(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_secret_value")
    body = json.dumps({"choices": [{"message": {"content": "ok"}}],
                       "usage": {"prompt_tokens": 3, "completion_tokens": 4}}).encode()
    op = StubOpener([(200, {}, body)])
    cfg = ModelConfig("g", "groq", "openai/gpt-oss-120b", k=1, extra={"reasoning_effort": "low"}, tier="llm")
    c = backends.make_backend(cfg, opener=op).complete(MSG, 0.0, 1.0, 1, 512)
    sent = json.loads(op.requests[0].data)
    assert sent["reasoning_effort"] == "low" and sent["model"] == "openai/gpt-oss-120b"
    assert op.requests[0].get_header("Authorization") == "Bearer gsk_secret_value"
    assert c.text == "ok" and c.completion_tokens == 4


def test_groq_429_raises_rate_limited(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_secret_value")
    op = StubOpener([(429, {"retry-after": "17"}, b"{}")])
    cfg = ModelConfig("g", "groq", "llama-3.3-70b-versatile", k=1, tier="llm")
    with pytest.raises(backends.RateLimited) as e:
        backends.make_backend(cfg, opener=op).complete(MSG, 0.0, 1.0, 1, 10)
    assert e.value.retry_after_s == 17


def test_groq_key_never_in_repr_or_errors(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_secret_value")
    op = StubOpener([(400, {}, b'{"error": "bad"}')])
    cfg = ModelConfig("g", "groq", "llama-3.3-70b-versatile", k=1, tier="llm")
    b = backends.make_backend(cfg, opener=op)
    assert "gsk_secret_value" not in repr(b)
    with pytest.raises(backends.BackendError) as e:
        b.complete(MSG, 0.0, 1.0, 1, 10)
    assert "gsk_secret_value" not in str(e.value)


def test_groq_missing_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    cfg = ModelConfig("g", "groq", "llama-3.3-70b-versatile", k=1, tier="llm")
    with pytest.raises(backends.BackendError):
        backends.make_backend(cfg, opener=StubOpener([]))
