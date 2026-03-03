"""Claude API client wrapper."""

import os
import time
from typing import Optional

from anthropic import Anthropic, APIStatusError, RateLimitError


# Fallback when models API fails; use ANTHROPIC_MODEL env to override
FALLBACK_MODEL = "claude-haiku-4-5"
MAX_RETRIES = 3
RETRY_DELAY = 2.0
_MODEL_CACHE: Optional[tuple[float, str]] = None
_MODEL_CACHE_TTL = 3600  # 1 hour

# Per-million-token pricing (input, output) in USD. Anthropic publishes these; no cost API.
# https://docs.anthropic.com/en/docs/about-claude/pricing
PRICING_PER_1M = {
    "opus": (5.0, 25.0),      # Claude Opus 4.x
    "sonnet": (3.0, 15.0),    # Claude Sonnet 4.x
    "haiku": (1.0, 5.0),      # Claude Haiku 4.x
}


def _cost_from_usage(usage, model: str) -> float:
    """Compute USD cost from usage and model name."""
    input_tokens = getattr(usage, "input_tokens", 0) or 0
    output_tokens = getattr(usage, "output_tokens", 0) or 0
    model_lower = model.lower()
    if "opus" in model_lower:
        inp, out = PRICING_PER_1M["opus"]
    elif "sonnet" in model_lower:
        inp, out = PRICING_PER_1M["sonnet"]
    else:
        inp, out = PRICING_PER_1M["haiku"]
    return (input_tokens / 1e6) * inp + (output_tokens / 1e6) * out


def _get_client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. Set it in your environment or .env file."
        )
    return Anthropic(api_key=api_key)


def get_available_model(prefer: str = "sonnet") -> str:
    """
    Query Anthropic API for available models and return the best match.
    prefer: "haiku" (fast), "sonnet" (default), or "opus" (strongest).
    Caches result for 1 hour.
    """
    global _MODEL_CACHE
    now = time.time()
    if _MODEL_CACHE and (now - _MODEL_CACHE[0]) < _MODEL_CACHE_TTL:
        return _MODEL_CACHE[1]

    env_model = (os.environ.get("ANTHROPIC_MODEL") or "").strip()
    if env_model:
        try:
            client = _get_client()
            page = client.models.list(limit=100)
            ids = [m.id for m in page.data]
            if env_model in ids:
                _MODEL_CACHE = (now, env_model)
                return env_model
        except Exception:
            pass
        return env_model  # Use env value even if not in list (e.g. new model)

    try:
        client = _get_client()
        page = client.models.list(limit=100)
        ids = [m.id for m in page.data]
        prefer_lower = prefer.lower()
        for mid in ids:
            if prefer_lower in mid.lower():
                _MODEL_CACHE = (now, mid)
                return mid
        if ids:
            _MODEL_CACHE = (now, ids[0])
            return ids[0]
    except Exception:
        pass
    return FALLBACK_MODEL


def complete(
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
) -> tuple[str, float]:
    """
    Send a prompt to Claude and return the text response and cost in USD.

    Args:
        prompt: The user message.
        system: Optional system prompt.
        model: Model to use (default: queried from API, prefers haiku).

    Returns:
        Tuple of (text response, cost_usd). Cost is computed from usage tokens.

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set.
        APIStatusError: On API errors after retries.
    """
    client = _get_client()
    model = model or get_available_model(prefer="sonnet")

    for attempt in range(MAX_RETRIES):
        try:
            kwargs: dict = {
                "model": model,
                "max_tokens": 8192,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system

            response = client.messages.create(**kwargs)
            cost = _cost_from_usage(response.usage, model)
            return response.content[0].text, cost

        except RateLimitError:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise
        except APIStatusError:
            raise
