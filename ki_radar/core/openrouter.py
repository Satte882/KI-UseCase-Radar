from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from django.conf import settings

MAX_OPENROUTER_RESPONSE_BYTES = 2_000_000


class OpenRouterUnavailable(RuntimeError):
    def __init__(self, message: str, *, code: str = "unavailable") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class OpenRouterResult:
    content: str
    model: str
    usage: dict[str, object]
    output_chars: int


def _setting(name: str, default: str = "") -> str:
    return str(getattr(settings, name, os.getenv(name, default)) or "")


def _usage_metadata(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        return {}
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return {}
    allowed = ("prompt_tokens", "completion_tokens", "total_tokens", "cost")
    return {name: usage.get(name) for name in allowed if usage.get(name) is not None}


def _api_url() -> str:
    api_url = _setting(
        "OPENROUTER_API_URL",
        "https://openrouter.ai/api/v1/chat/completions",
    )
    parsed_url = urllib.parse.urlparse(api_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise OpenRouterUnavailable(
            "Die OpenRouter API-URL muss eine gültige HTTPS-URL sein.",
            code="invalid_configuration",
        )
    return api_url


def _headers(api_key: str) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-OpenRouter-Title": _setting("OPENROUTER_APP_NAME", "KI-Radar"),
    }
    site_url = _setting("OPENROUTER_SITE_URL")
    if site_url:
        headers["HTTP-Referer"] = site_url
    return headers


def _read_bounded(response) -> bytes:
    payload = response.read(MAX_OPENROUTER_RESPONSE_BYTES + 1)
    if len(payload) > MAX_OPENROUTER_RESPONSE_BYTES:
        raise OpenRouterUnavailable(
            "OpenRouter hat eine zu große Antwort zurückgegeben.",
            code="response_too_large",
        )
    return payload


def request_openrouter(
    *,
    messages: list[dict[str, str]],
    max_tokens: int,
    timeout_seconds: int,
    temperature: float = 0.1,
    response_format: dict[str, Any] | None = None,
) -> OpenRouterResult:
    api_key = _setting("OPENROUTER_API_KEY")
    if not api_key:
        raise OpenRouterUnavailable(
            "Kein OpenRouter API-Key konfiguriert.",
            code="not_configured",
        )

    model = _setting("OPENROUTER_MODEL")
    body: dict[str, Any] = {
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if model:
        body["model"] = model
    if response_format is not None:
        body["response_format"] = response_format

    request = urllib.request.Request(  # noqa: S310
        _api_url(),
        data=json.dumps(body).encode("utf-8"),
        headers=_headers(api_key),
        method="POST",
    )
    try:
        with urllib.request.urlopen(  # nosec B310  # noqa: S310
            request,
            timeout=timeout_seconds,
        ) as response:
            payload = json.loads(_read_bounded(response).decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            code = "rate_limit"
            message = "OpenRouter hat das Aufruflimit erreicht. Bitte später erneut versuchen."
        elif exc.code in {401, 403}:
            code = "unauthorized"
            message = "OpenRouter ist nicht korrekt autorisiert."
        elif 500 <= exc.code <= 599:
            code = "provider_unavailable"
            message = "OpenRouter ist derzeit nicht verfügbar."
        else:
            code = "provider_error"
            message = "Die OpenRouter-Anfrage wurde abgelehnt."
        raise OpenRouterUnavailable(message, code=code) from exc
    except TimeoutError as exc:
        raise OpenRouterUnavailable(
            "Die OpenRouter-Anfrage hat das Zeitlimit überschritten.",
            code="timeout",
        ) from exc
    except urllib.error.URLError as exc:
        raise OpenRouterUnavailable(
            "OpenRouter ist derzeit nicht erreichbar.",
            code="provider_unavailable",
        ) from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OpenRouterUnavailable(
            "OpenRouter hat ein ungültiges Antwortformat zurückgegeben.",
            code="invalid_response",
        ) from exc

    usage = _usage_metadata(payload)
    try:
        content = payload["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise OpenRouterUnavailable(
            "OpenRouter hat ein unerwartetes Antwortformat zurückgegeben.",
            code="invalid_response",
        ) from exc
    if not content:
        raise OpenRouterUnavailable(
            "OpenRouter hat keine Analyse zurückgegeben.",
            code="empty_response",
        )
    returned_model = payload.get("model") if isinstance(payload, dict) else ""
    return OpenRouterResult(
        content=content,
        model=str(returned_model or model),
        usage=usage,
        output_chars=len(content),
    )
