"""Fixed experiment settings. Values come from the design doc (sections 4-6)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

SINCE = "2025-01-01"
LCB_URL = "https://huggingface.co/datasets/livecodebench/code_generation_lite/resolve/main/{name}"
LCB_FILES = ["test5.jsonl", "test6.jsonl", "test7.jsonl", "test8.jsonl"]  # missing ones are skipped

SAMPLE_TEMPERATURE = 0.8
SAMPLE_TOP_P = 0.95
TIMEOUT_S = 6.0
TIMEOUT_HARD_S = 12.0
N_SELFTESTS = 5
TAUS = [0.6, 0.8, 1.0]
PRIMARY_TAU = 1.0

OLLAMA_URL = "http://localhost:11434"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


@dataclass(frozen=True)
class ModelConfig:
    name: str
    provider: Literal["ollama", "groq", "fake"]
    model: str
    k: int
    think: Optional[bool] = None
    max_tokens: int = 1024
    extra: dict = field(default_factory=dict, hash=False, compare=False)
    tier: Literal["slm", "llm"] = "slm"


SLM_CONFIGS = [
    ModelConfig("qwen2.5-coder-1.5b", "ollama", "qwen2.5-coder:1.5b", k=5),
    ModelConfig("qwen2.5-coder-7b", "ollama", "qwen2.5-coder:7b", k=5),
    ModelConfig("deepseek-coder-6.7b", "ollama", "deepseek-coder:6.7b", k=5),
    ModelConfig("qwen3-4b-nothink", "ollama", "qwen3:4b", k=5, think=False),
    ModelConfig("qwen3-4b-think", "ollama", "qwen3:4b", k=2, think=True, max_tokens=8192),
]

LLM_CONFIGS = [
    ModelConfig("gpt-oss-120b", "groq", "openai/gpt-oss-120b", k=1, max_tokens=8192,
                extra={"reasoning_effort": "low"}, tier="llm"),
    ModelConfig("llama-3.3-70b", "groq", "llama-3.3-70b-versatile", k=1, tier="llm"),
]

ALL_CONFIGS = SLM_CONFIGS + LLM_CONFIGS


def get_config(name: str) -> ModelConfig:
    for c in ALL_CONFIGS:
        if c.name == name:
            return c
    raise KeyError(f"unknown config {name!r}; known: {[c.name for c in ALL_CONFIGS]}")
