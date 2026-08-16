from __future__ import annotations

import re
from dataclasses import dataclass

from .models import ProcessAnalysis

SOURCE_LABELS = {
    "bottlenecks": "Bottlenecks und Ursachen",
    "baseline_metrics": "Baseline und Prozesskennzahlen",
    "roles": "Rollen und Verantwortlichkeiten",
    "systems": "Anwendungen und Arbeitsmittel",
    "business_rules": "Geschäftsregeln",
    "handoffs": "Übergaben und Schnittstellen",
    "exceptions": "Ausnahmen und Fehlerfälle",
    "target_state_principles": "Prinzipien für den Soll-Prozess",
    "status": "Validierungsstatus",
}
ASSUMPTION_MARKERS = (
    "annahme",
    "offen",
    "zu prüfen",
    "unklar",
    "noch zu klären",
)


@dataclass(frozen=True)
class ProcessFinding:
    text: str
    source_field: str
    source_label: str
    source_anchor: str
    priority: int
    context_label: str = ""
    is_assumption: bool = False


@dataclass(frozen=True)
class ProcessFindingGroup:
    key: str
    label: str
    items: tuple[ProcessFinding, ...]


def _split_entries(value: str, *, limit: int) -> tuple[str, ...]:
    text = str(value or "").strip()
    if not text:
        return ()

    lines = [
        re.sub(r"^[\s\-\u2013\u2014\u2022*\d.)]+", "", line).strip()
        for line in text.splitlines()
        if line.strip()
    ]
    if len(lines) == 1 and ";" in lines[0]:
        lines = [part.strip() for part in lines[0].split(";") if part.strip()]
    return tuple(lines[:limit])


def _findings_for_field(
    process_analysis: ProcessAnalysis,
    field_name: str,
    *,
    limit: int,
    start_priority: int,
    context_label: str = "",
) -> tuple[ProcessFinding, ...]:
    return tuple(
        ProcessFinding(
            text=text,
            source_field=field_name,
            source_label=SOURCE_LABELS[field_name],
            source_anchor=f"analysis-{field_name.replace('_', '-')}",
            priority=start_priority + index,
            context_label=context_label,
        )
        for index, text in enumerate(
            _split_entries(getattr(process_analysis, field_name, ""), limit=limit)
        )
    )


def _assumption_findings(process_analysis: ProcessAnalysis) -> tuple[ProcessFinding, ...]:
    findings = []
    priority = 1
    for field_name in (
        "business_rules",
        "handoffs",
        "exceptions",
        "target_state_principles",
    ):
        for text in _split_entries(getattr(process_analysis, field_name, ""), limit=5):
            if not text.casefold().startswith(ASSUMPTION_MARKERS):
                continue
            findings.append(
                ProcessFinding(
                    text=text,
                    source_field=field_name,
                    source_label=SOURCE_LABELS[field_name],
                    source_anchor=f"analysis-{field_name.replace('_', '-')}",
                    priority=priority,
                    is_assumption=True,
                )
            )
            priority += 1

    if process_analysis.status != ProcessAnalysis.Status.VALIDATED:
        findings.append(
            ProcessFinding(
                text=(
                    f"Prozessversion v{process_analysis.version} ist noch nicht eigenständig "
                    "validiert."
                ),
                source_field="status",
                source_label=SOURCE_LABELS["status"],
                source_anchor="process-validation",
                priority=priority,
                is_assumption=True,
            )
        )
    return tuple(findings)


def build_process_findings(
    process_analysis: ProcessAnalysis,
) -> tuple[ProcessFindingGroup, ...]:
    groups = [
        ProcessFindingGroup(
            key="bottlenecks",
            label="Unstrukturierte Bottleneck- und Ursachenangaben",
            items=_findings_for_field(
                process_analysis,
                "bottlenecks",
                limit=3,
                start_priority=1,
            ),
        ),
        ProcessFindingGroup(
            key="metrics",
            label="Entscheidungsrelevante Kennzahlen",
            items=_findings_for_field(
                process_analysis,
                "baseline_metrics",
                limit=3,
                start_priority=1,
            ),
        ),
        ProcessFindingGroup(
            key="context",
            label="Betroffene Rollen und Systeme",
            items=(
                *_findings_for_field(
                    process_analysis,
                    "roles",
                    limit=2,
                    start_priority=1,
                    context_label="Rolle",
                ),
                *_findings_for_field(
                    process_analysis,
                    "systems",
                    limit=2,
                    start_priority=3,
                    context_label="System",
                ),
            ),
        ),
        ProcessFindingGroup(
            key="assumptions",
            label="Offene Annahmen und Prüfbedarf",
            items=_assumption_findings(process_analysis),
        ),
    ]
    return tuple(group for group in groups if group.items)
