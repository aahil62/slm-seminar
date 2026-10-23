"""Fixed experiment settings. Values come from the design doc (sections 4-6)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal, Optional

SINCE = "2025-01-01"
LCB_URL = "https://huggingface.co/datasets/livecodebench/code_generation_lite/resolve/main/{name}"
LCB_FILES = ["test5.jsonl", "test6.jsonl", "test7.jsonl", "test8.jsonl"]  # missing ones are skipped

MBPP_ROWS_URL = ("https://datasets-server.huggingface.co/rows?dataset=evalplus/mbppplus"
                 "&config=default&split=test&offset={offset}&length=100")
MBPP_SAMPLE = 200          # fixed random subset of MBPP+'s 378 problems (Groq daily-limit budget)
MBPP_SEED = 20261016
# Broken benchmark items: the reference solution fails its own hidden tests. Excluded before sampling.
MBPP_EXCLUDE = {
    590: "reference solution fails its plus test by a last-digit float difference (checked 2026-10-16)",
}

SAMPLE_TEMPERATURE = 0.8
SAMPLE_TOP_P = 0.95
TIMEOUT_S = 6.0
TIMEOUT_HARD_S = 12.0
N_SELFTESTS = 5
TAUS = [0.6, 0.8, 1.0]
PRIMARY_TAU = 1.0

OLLAMA_URL = os.environ.get("SLMCHECK_OLLAMA_URL", "http://localhost:11434")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEEPINFRA_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
SAMBANOVA_URL = "https://api.sambanova.ai/v1/chat/completions"


@dataclass(frozen=True)
class ModelConfig:
    name: str
    provider: Literal["ollama", "groq", "deepinfra", "sambanova", "fake"]
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
    # "qwen3:4b" now resolves to Qwen3-4B-Thinking-2507, which cannot turn thinking off. The explicit tag
    # below is the original hybrid Qwen3-4B (40K context) where think=False/True works (see VERIFICATION_NOTES).
    ModelConfig("qwen3-4b-nothink", "ollama", "qwen3:4b-q4_K_M", k=5, think=False),
    ModelConfig("qwen3-4b-think", "ollama", "qwen3:4b-q4_K_M", k=1, think=True, max_tokens=8192),
]

LLM_CONFIGS = [
    ModelConfig("gpt-oss-120b", "groq", "openai/gpt-oss-120b", k=1, max_tokens=8192,
                extra={"reasoning_effort": "low"}, tier="llm"),
    # llama-3.3-70b-versatile dropped (agreed fallback): Groq returned 404 model_not_found on 2026-10-23.
    # ModelConfig("llama-3.3-70b", "groq", "llama-3.3-70b-versatile", k=1, tier="llm"),
    # 2026-10-23 history of the second cloud model: llama-3.3-70b was Enterprise-only on Groq, retired on
    # NVIDIA (2026-08-26), $5 prepay on DeepInfra (declined), and SambaNova answered HTTP 429 "high demand"
    # for ~3 h (13:13-16:13, 0 samples). DeepSeek-V3.1 on SambaNova was used instead.
    # ModelConfig("llama-3.3-70b", "sambanova", "Meta-Llama-3.3-70B-Instruct", k=1, tier="llm"),
    # DeepSeek-V3.1 is hybrid; SambaNova serves it non-thinking by default (probe: no reasoning field, no
    # <think> text, identical output with chat_template_kwargs enable_thinking=False), so no flag is sent.
    # Released Aug 2025, after the LiveCodeBench window: contamination caveat, see VERIFICATION_NOTES.
    ModelConfig("deepseek-v3.1", "sambanova", "DeepSeek-V3.1", k=1, tier="llm"),
]

ALL_CONFIGS = SLM_CONFIGS + LLM_CONFIGS


def get_config(name: str) -> ModelConfig:
    for c in ALL_CONFIGS:
        if c.name == name:
            return c
    raise KeyError(f"unknown config {name!r}; known: {[c.name for c in ALL_CONFIGS]}")
