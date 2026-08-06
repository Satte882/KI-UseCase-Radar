from __future__ import annotations

import os

from django.conf import settings

_TRUTHY_VALUES = {"1", "true", "yes", "on"}


def field_adoption_enabled() -> bool:
    """Return the server-side Block-5 feature state; disabled by default."""
    configured = getattr(settings, "ACCELERATOR_FIELD_ADOPTION_ENABLED", None)
    if configured is not None:
        return bool(configured)
    raw_value = os.getenv("ACCELERATOR_FIELD_ADOPTION_ENABLED", "false")
    return raw_value.strip().lower() in _TRUTHY_VALUES
