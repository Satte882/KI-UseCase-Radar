from __future__ import annotations

import sys

from . import services
from .architecture_artifacts import get_delivery_architecture_artifacts

ORIGINAL_MISSING_READY_FIELDS = services.missing_ready_fields
ORIGINAL_RENDER_DELIVERY_MARKDOWN = services.render_delivery_markdown

EXPLICIT_HANDOVER_FIELDS = {
    "integrations": "Schnittstellen und Integrationen",
    "dependencies": "Abhängigkeiten",
    "risks": "Risiken",
    "assumptions": "Annahmen",
    "architecture_decisions": "Architekturentscheidungen und Leitplanken",
}


def missing_ready_fields(package) -> list[str]:
    missing = list(ORIGINAL_MISSING_READY_FIELDS(package))
    for field_name, label in EXPLICIT_HANDOVER_FIELDS.items():
        if not str(getattr(package, field_name, "")).strip():
            missing.append(label)
    artifacts = get_delivery_architecture_artifacts(package)
    if artifacts is None:
        missing.extend(
            [
                "Ist-/Ziel-Systemlandschaft",
                "Daten- und Informationsflüsse",
                "Integrationsverträge und Verantwortlichkeiten",
            ]
        )
    else:
        missing.extend(artifacts.missing_ready_fields)
    return list(dict.fromkeys(missing))


def render_delivery_markdown(package) -> str:
    base = ORIGINAL_RENDER_DELIVERY_MARKDOWN(package).rstrip()
    artifacts = get_delivery_architecture_artifacts(package)
    if artifacts is None:
        return base + "\n"
    sections = [
        ("Ist-/Ziel-Systemlandschaft", artifacts.system_landscape),
        ("Daten- und Informationsflüsse", artifacts.data_flows),
        ("Integrationsverträge und Verantwortlichkeiten", artifacts.integration_contracts),
        ("Architekturartefakte und Diagramme", artifacts.artifacts_url),
    ]
    appendix = "\n\n".join(f"## {title}\n\n{content or '-'}" for title, content in sections)
    return f"{base}\n\n{appendix}\n"


def install() -> None:
    services.missing_ready_fields = missing_ready_fields
    services.render_delivery_markdown = render_delivery_markdown
    journey_module = sys.modules.get("ki_radar.use_cases.journey")
    if journey_module is not None:
        journey_module.missing_ready_fields = missing_ready_fields
