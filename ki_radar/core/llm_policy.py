from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.conf import settings


class LLMConfigurationError(RuntimeError):
    """Raised when an Accelerator LLM setting is invalid."""


@dataclass(frozen=True)
class AcceleratorLLMPolicy:
    timeout_seconds: int
    max_input_chars: int
    max_output_tokens: int
    max_calls_per_context: int
    max_calls_per_user_day: int
    max_calls_global_day: int


_SETTING_BOUNDS = {
    "ACCELERATOR_LLM_TIMEOUT_SECONDS": (1, 120),
    "ACCELERATOR_LLM_MAX_INPUT_CHARS": (1, 100_000),
    "ACCELERATOR_LLM_MAX_OUTPUT_TOKENS": (1, 4_096),
    "ACCELERATOR_LLM_MAX_CALLS_PER_CONTEXT": (1, 50),
    "ACCELERATOR_LLM_MAX_CALLS_PER_USER_DAY": (1, 1_000),
    "ACCELERATOR_LLM_MAX_CALLS_GLOBAL_DAY": (1, 100_000),
}


def _positive_int(name: str, value: Any) -> int:
    lower, upper = _SETTING_BOUNDS[name]
    if isinstance(value, bool):
        raise LLMConfigurationError(f"{name} muss eine ganze Zahl sein.")
    raw = str(value).strip()
    try:
        parsed = int(raw)
    except (TypeError, ValueError) as exc:
        raise LLMConfigurationError(f"{name} muss eine ganze Zahl sein.") from exc
    if not lower <= parsed <= upper:
        raise LLMConfigurationError(f"{name} muss zwischen {lower} und {upper} liegen.")
    return parsed


def get_accelerator_llm_policy() -> AcceleratorLLMPolicy:
    """Return the validated, repository-wide Accelerator LLM limits.

    Request-count limits are configuration contracts for the later persistent
    Capture/Suggestion context. Block 1 immediately enforces timeout, input and
    output limits; persistent quota counting is introduced with that context.
    """

    values = {name: _positive_int(name, getattr(settings, name)) for name in _SETTING_BOUNDS}
    context_limit = values["ACCELERATOR_LLM_MAX_CALLS_PER_CONTEXT"]
    user_limit = values["ACCELERATOR_LLM_MAX_CALLS_PER_USER_DAY"]
    global_limit = values["ACCELERATOR_LLM_MAX_CALLS_GLOBAL_DAY"]
    if context_limit > user_limit:
        raise LLMConfigurationError(
            "ACCELERATOR_LLM_MAX_CALLS_PER_CONTEXT darf die nutzerbezogene "
            "Tagesgrenze nicht überschreiten."
        )
    if user_limit > global_limit:
        raise LLMConfigurationError(
            "ACCELERATOR_LLM_MAX_CALLS_PER_USER_DAY darf die globale "
            "Tagesgrenze nicht überschreiten."
        )
    return AcceleratorLLMPolicy(
        timeout_seconds=values["ACCELERATOR_LLM_TIMEOUT_SECONDS"],
        max_input_chars=values["ACCELERATOR_LLM_MAX_INPUT_CHARS"],
        max_output_tokens=values["ACCELERATOR_LLM_MAX_OUTPUT_TOKENS"],
        max_calls_per_context=context_limit,
        max_calls_per_user_day=user_limit,
        max_calls_global_day=global_limit,
    )
