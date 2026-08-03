from __future__ import annotations

from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from ki_radar.use_cases.models import ApprovalDecision, UseCase

from .exports import render_delivery_markdown
from .models import (
    DELIVERY_SECTION_DEFINITIONS,
    DeliveryPackage,
    DeliveryRoleSourceDecision,
    DeliverySectionReview,
)
from .permissions import (
    can_resolve_role_source,
    can_use_admin_confirmation_override,
    confirmation_role_label,
    reviewer_roles,
)
from .readiness import blocking_findings, missing_ready_fields

APPROVED_STATUSES = {
    UseCase.DecisionStatus.APPROVED,
    UseCase.DecisionStatus.APPROVED_WITH_CONDITIONS,
}

SECTION_ORIGINS = {
    "problem_and_target": DeliverySectionReview.ContentOrigin.INHERITED,
    "scope_and_users": DeliverySectionReview.ContentOrigin.INHERITED,
    "solution_direction": DeliverySectionReview.ContentOrigin.MIXED,
    "architecture_and_data": DeliverySectionReview.ContentOrigin.MIXED,
    "requirements_and_governance": DeliverySectionReview.ContentOrigin.NEW,
    "acceptance_and_measurement": DeliverySectionReview.ContentOrigin.MIXED,
    "delivery_control": DeliverySectionReview.ContentOrigin.MIXED,
}

TECHNICAL_OWNER_ADOPTION_RESET_SECTIONS = {
    "solution_direction",
    "architecture_and_data",
    "requirements_and_governance",
    "delivery_control",
}


def latest_final_approval(use_case: UseCase) -> ApprovalDecision | None:
    return (
        use_case.approval_decisions.filter(
            decision_status__in=APPROVED_STATUSES,
            finalized_at__isnull=False,
        )
        .select_related("assessment", "decided_by", "second_approved_by")
        .first()
    )


def current_delivery_package(use_case: UseCase) -> DeliveryPackage | None:
    """Return the latest Delivery Package version for the Use Case."""

    return DeliveryPackage.objects.filter(use_case_id=use_case.pk).first()


def current_handed_over_package(use_case: UseCase) -> DeliveryPackage | None:
    """Return the current package only when its handover is complete and timestamped."""

    package = current_delivery_package(use_case)
    if (
        package is not None
        and package.status == DeliveryPackage.Status.HANDED_OVER
        and package.handed_over_at is not None
    ):
        return package
    return None


def delivery_eligibility(use_case: UseCase) -> tuple[bool, str, ApprovalDecision | None]:
    if use_case.decision_status not in APPROVED_STATUSES:
        return False, "Der Use Case besitzt keine finale positive Freigabe.", None
    decision = latest_final_approval(use_case)
    if decision is None:
        return False, "Die positive Freigabe ist noch nicht final dokumentiert.", None
    return True, "", decision


def _iso(value: datetime | None) -> str:
    return value.isoformat() if value else ""


def _source_entry(source, *, version=None) -> dict[str, str | int | None]:
    if source is None:
        return {}
    entry: dict[str, str | int | None] = {
        "id": str(source.pk),
        "updated_at": _iso(getattr(source, "updated_at", None)),
    }
    if version is not None:
        entry["version"] = version
    return entry


def _field_source(*, kind: str, label: str, source, field: str, value=None) -> dict:
    raw_value = getattr(source, field) if value is None else value
    return {
        "kind": kind,
        "label": label,
        "id": str(source.pk),
        "field": field,
        "value": "" if raw_value is None else str(raw_value),
        "updated_at": _iso(getattr(source, "updated_at", None)),
    }


def _origin_context(use_case: UseCase):
    try:
        origin = use_case.architecture_origin
    except ObjectDoesNotExist:
        return None, None, None
    return origin, origin.process_analysis, origin.solution_option


def build_delivery_field_sources(use_case: UseCase) -> dict[str, dict]:
    origin, _process, _option = _origin_context(use_case)
    sources = {
        "problem_context": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="problem_statement",
        ),
        "target_outcome": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="expected_benefit",
        ),
        "users_and_scenarios": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="intended_users" if use_case.intended_users else "target_users",
        ),
        "solution_outline": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="intended_purpose" if use_case.intended_purpose else "summary",
        ),
        "system_context": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="source_systems",
        ),
        "data_context": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="data_sources",
        ),
        "integrations": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="interface_description",
        ),
        "human_oversight": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="human_oversight",
        ),
        "operations_and_support": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="support_responsibility",
        ),
    }
    if origin is not None:
        sources["in_scope"] = _field_source(
            kind="value_stream",
            label="Value Stream",
            source=origin.stage.value_stream,
            field="scope_in",
        )
        sources["out_of_scope"] = _field_source(
            kind="value_stream",
            label="Value Stream",
            source=origin.stage.value_stream,
            field="scope_out",
        )
    else:
        sources["in_scope"] = _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="summary" if use_case.summary else "affected_process",
        )
    return sources


def build_source_manifest(use_case: UseCase, decision: ApprovalDecision) -> dict:
    origin, process, option = _origin_context(use_case)
    manifest = {
        "use_case": _source_entry(use_case),
        "assessment": _source_entry(decision.assessment, version=decision.assessment.version),
        "approval": _source_entry(decision),
        "field_sources": build_delivery_field_sources(use_case),
        "role_sources": {
            "business_owner": {
                "id": str(use_case.business_owner_id or ""),
                "value": str(use_case.business_owner or ""),
            },
            "technical_owner": {
                "id": str(use_case.technical_owner_id or ""),
                "value": str(use_case.technical_owner or ""),
                "updated_at": _iso(use_case.updated_at),
                "adoption": "copied",
            },
        },
    }
    if origin is not None:
        manifest.update(
            {
                "value_stream": _source_entry(origin.stage.va²È="25•µ½Ù•ÁÉ•™¥à ‰½¹™¥Éµ|ˆ¤(€€€€€€€¥˜É½±”¹½Ð¥¸É½±•Ì½ÈÉ½±”¹½Ð¥¸É•Ù¥•Ü¹É•ÅÕ¥É•‘}½¹™¥Éµ…Ñ¥½¹Ìè(€€€€€€€€€€€É½±•}±…‰•°€ô€‰™…¡±¥¡”ˆ¥˜É½±”€ôô€‰‰ÕÍ¥¹•ÍÌˆ•±Í”€‰Ñ•¡¹¥Í¡”ˆ(€€€€€€€€€€€É…¥Í”Y…±¥‘…Ñ¥½¹ÉÉ½È¡˜‰ñÈ‘¥”íÉ½±•}±…‰•±ô	•ÍÓ‘Ñ¥Õ¹œ™•¡±Ð‘¥”	•É•¡Ñ¥Õ¹œ¸ˆ¤((€€€€€€€½Ñ¡•É}É½±”€ô€‰Ñ•¡¹¥…°ˆ¥˜É½±”€ôô€‰‰ÕÍ¥¹•ÍÌˆ•±Í”€‰‰ÕÍ¥¹•ÍÌˆ(€€€€€€€½Ñ¡•É}…Ñ½É}¥€ô•Ñ…ÑÑÈ¡É•Ù¥•Ü°˜‰í½Ñ¡•É}É½±•õ}½¹™¥Éµ•‘}‰å}¥ˆ¤(€€€€€€€¥˜½Ñ¡•É}…Ñ½É}¥€ôô…Ñ½È¹¥è(€€€€€€€€€€€¥˜¹½Ð…¹}ÕÍ•}…‘µ¥¹}½¹™¥Éµ…Ñ¥½¹}½Ù•ÉÉ¥‘”¡…Ñ½È¤è(€€€€€€€€€€€€€€€É…¥Í”Y…±¥‘…Ñ¥½¹ÉÉ½È (€€€€€€€€€€€€€€€€€€€€‰¥•Í•±‰”A•ÉÍ½¸‘…É˜™…¡±¥ Õ¹Ñ•¡¹¥Í ¹ÕÈ…±ÌQ•¡¹¥Í¡•È€ˆ(€€€€€€€€€€€€€€€€€€€€‰‘µ¥¹¥ÍÑÉ…Ñ½È›ñÈ‘µ¥¸´½‘•ÈQ•ÍÑéÝ•­”‰•ÍÓ‘Ñ¥•¸¸ˆ(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€½±±…ÁÍ•}É•…Í½¸€ôÉ½±•}½±±…ÁÍ•}É•…Í½¸¹ÍÑÉ¥À ¤(€€€€€€€€€€€¥˜¹½Ð½±±…ÁÍ•}É•…Í½¸è(€€€€€€€€€€€€€€€É…¥Í”Y…±¥‘…Ñ¥½¹ÉÉ½È (€€€€€€€€€€€€€€€€€€€€‰ñÈ‘¥”‘µ¥¸µM½¹‘•É‰•ÍÓ‘Ñ¥Õ¹œ¥ÍÐ•¥¹”	•Ëñ¹‘Õ¹œ•É™½É‘•É±¥ ¸ˆ(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€É•Ù¥•Ü¹É½±•}½±±…ÁÍ•}É•…Í½¸€ô½±±…ÁÍ•}É•…Í½¸(€€€€€€€€€€€É•Ù¥•Ü¹…‘µ¥¹}½Ù•ÉÉ¥‘•}½¹™¥Éµ•€ôQÉÕ”(€€€€€€€•±Í”è(€€€€€€€€€€€É•Ù¥•Ü¹É½±•}½±±…ÁÍ•}É•…Í½¸€ô€ˆˆ(€€€€€€€€€€€É•Ù¥•Ü¹…‘µ¥¹}½Ù•ÉÉ¥‘•}½¹™¥Éµ•€ô…±Í”((€€€€€€€…ÍÍ¥¹•‘}½Ý¹•É}¥€ô€ (€€€€€€€€€€€Á…­…”¹ÕÍ•}…Í”¹‰ÕÍ¥¹•ÍÍ}½Ý¹•É}¥¥˜É½±”€ôô€‰‰ÕÍ¥¹•ÍÌˆ•±Í”Á…­…”¹Ñ•¡¹¥…±}½Ý¹•É}¥(€€€€€€€€¤(€€€€€€€Í•Ñ…ÑÑÈ¡É•Ù¥•Ü°˜‰íÉ½±•õ}½¹™¥Éµ•‘}‰äˆ°…Ñ½È¤(€€€€€€€Í•Ñ…ÑÑÈ¡É•Ù¥•Ü°˜‰íÉ½±•õ}½¹™¥Éµ•‘}…Ðˆ°¹½Ü¤(€€€€€€€Í•Ñ…ÑÑÈ (€€€€€€€€€€€É•Ù¥•Ü°(€€€€€€€€€€€˜‰íÉ½±•õ}½¹™¥Éµ…Ñ¥½¹}É½±”ˆ°(€€€€€€€€€€€½¹™¥Éµ…Ñ¥½¹}É½±•}±…‰•° (€€€€€€€€€€€€€€€É½±”°(€€€€€€€€€€€€€€€…ÍÍ¥¹•õ…ÍÍ¥¹•‘}½Ý¹•É}¥€ôô…Ñ½È¹¥°(€€€€€€€€€€€€€€€…‘µ¥¹}½Ù•ÉÉ¥‘”õÉ•Ù¥•Ü¹…‘µ¥¹}½Ù•ÉÉ¥‘•}½¹™¥Éµ•°(€€€€€€€€€€€€¤°(€€€€€€€€¤(€€€€€€€¥˜É•Ù¥•Ü¹…‘µ¥¹}½Ù•ÉÉ¥‘•}½¹™¥Éµ•è(€€€€€€€€€€€É•Ù¥•Ü¹‰ÕÍ¥¹•ÍÍ}½¹™¥Éµ…Ñ¥½¹}É½±”€ô€‰‘µ¥¸µM½¹‘•É‰•ÍÓ‘Ñ¥Õ¹œˆ(€€€€€€€€€€€É•Ù¥•Ü¹Ñ•¡¹¥…±}½¹™¥Éµ…Ñ¥½¹}É½±”€ô€‰‘µ¥¸µM½¹‘•É‰•ÍÓ‘Ñ¥Õ¹œˆ(€€€€€€€É•Ù¥•Ü¹É•Ù¥•Ý}ÍÑ…ÑÕÌ€ô€ (€€€€€€€€€€€•±¥Ù•ÉåM•Ñ¥½¹I•Ù¥•Ü¹I•Ù¥•ÝMÑ…ÑÕÌ¹=9%I5(€€€€€€€€€€€¥˜É•Ù¥•Ü¹½¹™¥Éµ…Ñ¥½¹Í}½µÁ±•Ñ”(€€€€€€€€€€€•±Í”•±¥Ù•ÉåM•Ñ¥½¹I•Ù¥•Ü¹I•Ù¥•ÝMÑ…ÑÕÌ¹9M}IY%\(€€€€€€€€¤(€€€•±¥˜…Ñ¥½¸€ôô€‰‰±½¬ˆè(€€€€€€€¥˜¹½ÐÉ•Ù¥•Ü¹É•Ù¥•Ý}¹½Ñ”è(€€€€€€€€€€€É…¥Í”Y…±¥‘…Ñ¥½¹ÉÉ½È ‰ñÈ•¥¹”	±½­¥•ÉÕ¹œ¥ÍÐ•¥¹”	•Ëñ¹‘Õ¹œ•É™½É‘•É±¥ ¸ˆ¤(€€€€€€€É•Ù¥•Ü¹É•Ù¥•Ý}ÍÑ…ÑÕÌ€ô•±¥Ù•ÉåM•Ñ¥½¹I•Ù¥•Ü¹I•Ù¥•ÝMÑ…ÑÕÌ¹	1=-(€€€•±¥˜…Ñ¥½¸€ôô€‰¹½Ñ}…ÁÁ±¥…‰±”ˆè(€€€€€€€¥˜¹½ÐÉ•Ù¥•Ü¹É•Ù¥•Ý}¹½Ñ”è(€€€€€€€€€€€É…¥Í”Y…±¥‘…Ñ¥½¹ÉÉ½È ‰9¥¡Ñ…¹Ý•¹‘‰…É­•¥ÐµÕÍÌ‰•Ëñ¹‘•ÐÝ•É‘•¸¸ˆ¤(€€€€€€€É•Ù¥•Ü¹½¹Ñ•¹Ñ}½É¥¥¸€ô•±¥Ù•ÉåM•Ñ¥½¹I•Ù¥•Ü¹½¹Ñ•¹Ñ=É¥¥¸¹9=Q}AA1%	1(€€€€€€€É•Ù¥•Ü¹É•Ù¥•Ý}ÍÑ…ÑÕÌ€ô•±¥Ù•ÉåM•Ñ¥½¹I•Ù¥•Ü¹I•Ù¥•ÝMÑ…ÑÕÌ¹9=Q}AA1%	1(€€€•±¥˜…Ñ¥½¸€ôô€‰É•Í•Ðˆè(€€€€€€€É•Ù¥•Ü¹É•Ù¥•Ý}ÍÑ…ÑÕÌ€ô•±¥Ù•ÉåM•Ñ¥½¹I•Ù¥•Ü¹I•Ù¥•ÝMÑ…ÑÕÌ¹9M}IY%\(€€€€€€€É•Ù¥•Ü¹‰ÕÍ¥¹•ÍÍ}½¹™¥Éµ•‘}‰ä€ô9½¹”(€€€€€€€É•Ù¥•Ü¹‰ÕÍ¥¹•ÍÍ}½¹™¥Éµ•‘}…Ð€ô9½¹”(€€€€€€€É•Ù¥•Ü¹Ñ•¡¹¥…±}½¹™¥Éµ•‘}‰ä€ô9½¹”(€€€€€€€É•Ù¥•Ü¹Ñ•¡¹¥…±}½¹™¥Éµ•‘}…Ð€ô9½¹”(€€€€€€€É•Ù¥•Ü¹‰ÕÍ¥¹•ÍÍ}½¹™¥Éµ…Ñ¥½¹}É½±”€ô€ˆˆ(€€€€€€€É•Ù¥•Ü¹Ñ•¡¹¥…±}½¹™¥Éµ…Ñ¥½¹}É½±”€ô€ˆˆ(€€€€€€€É•Ù¥•Ü¹É½±•}½±±…ÁÍ•}É•…Í½¸€ô€ˆˆ(€€€€€€€É•Ù¥•Ü¹…‘µ¥¹}½Ù•ÉÉ¥‘•}½¹™¥Éµ•€ô…±Í”(€€€•±Í”è(€€€€€€€É…¥Í”Y…±¥‘…Ñ¥½¹ÉÉ½È ‰U¹‰•­…¹¹Ñ”­Ñ¥½¸›ñÈ‘¥”M•­Ñ¥½¹ÍÁËñ™Õ¹œ¸ˆ¤((€€€É•Ù¥•Ü¹Í…Ù” ¤(€€€¥˜Á…­…”¹ÍÑ…ÑÕÌ€ôô•±¥Ù•ÉåA…­…”¹MÑ…ÑÕÌ¹Idè(€€€€€€€Á…­…”¹ÍÑ…ÑÕÌ€ô•±¥Ù•ÉåA…­…”¹MÑ…ÑÕÌ¹IP(€€€€€€€Á…­…”¹Í…Ù”¡ÕÁ‘…Ñ•}™¥•±‘Ìõl‰ÍÑ…ÑÕÌˆ°€‰ÕÁ‘…Ñ•‘}…Ð‰t¤(€€€É•ÑÕÉ¸É•Ù¥•Ü(()ÑÉ…¹Í…Ñ¥½¸¹…Ñ½µ¥Œ)‘•˜É•Í½±Ù•}Ñ•¡¹¥…±}½Ý¹•É}Í½ÕÉ•}¡…¹” (€€€€¨°(€€€Á…­…”è•±¥Ù•ÉåA…­…”°(€€€…Ñ¥½¸èÍÑÈ°(€€€É…Ñ¥½¹…±”èÍÑÈ°(€€€…Ñ½È°(¤€´ø•±¥Ù•ÉåI½±•M½ÕÉ••¥Í¥½¸è(€€€¥˜¹½Ð…¹}É•Í½±Ù•}É½±•}Í½ÕÉ”¡…Ñ½È°Á…­…”¤è(€€€€€€€É…¥Í”Y…±¥‘…Ñ¥½¹ÉÉ½È ‰ñÈ‘¥•Í”¹ÑÍ¡•¥‘Õ¹œéÕÈI½±±•¹ÅÕ•±±”™•¡±Ð‘¥”	•É•¡Ñ¥Õ¹œ¸ˆ¤(€€€Á…­…”€ô•±¥Ù•ÉåA…­…”¹½‰©•ÑÌ¹Í•±•Ñ}™½É}ÕÁ‘…Ñ” ¤¹•Ð¡Á¬õÁ…­…”¹Á¬¤(€€€¥˜Á…­…”¹ÍÑ…ÑÕÌ€ôô•±¥Ù•ÉåA…­…”¹MÑ…ÑÕÌ¹!9}=YHè(€€€€€€€É…¥Í”Y…±¥‘…Ñ¥½¹ÉÉ½È ‰¥¸ƒñ‰•É•‰•¹•Ì•±¥Ù•ÉäA…­…”¥ÍÐÕ¹Ù•Ë‘¹‘•É±¥ ¸ˆ¤(€€€É•…Í½¸€ôÉ…Ñ¥½¹…±”¹ÍÑÉ¥À ¤(€€€¥˜¹½ÐÉ•…Í½¸è(€€€€€€€É…¥Í”Y…±¥‘…Ñ¥½¹ÉÉ½È ‰ñÈ‘¥”ƒq‰•É¹…¡µ••¹ÑÍ¡•¥‘Õ¹œ¥ÍÐ•¥¹”	•Ëñ¹‘Õ¹œ•É™½É‘•É±¥ ¸ˆ¤(€€€ÍÑ…Ñ”€ôÑ•¡¹¥…±}½Ý¹•É}Í½ÕÉ•}ÍÑ…Ñ”¡Á…­…”¤(€€€¥˜ÍÑ…Ñ”¥Ì9½¹”½È¹½ÐÍÑ…Ñ•l‰Í½ÕÉ•}¡…¹•‰tè(€€€€€€€É…¥Í”Y…±¥‘…Ñ¥½¹ÉÉ½È ‰Ì±¥•Ð­•¥¹”½™™•¹”ƒ¹‘•ÉÕ¹œ‘•ÌQ•¡¹¥…°=Ý¹•ÉÌÙ½È¸ˆ¤(€€€¥˜…Ñ¥½¸¹½Ð¥¸ì(€€€€€€€•±¥Ù•ÉåI½±•M½ÕÉ••¥Í¥½¸¹•¥Í¥½¸¹=AQ}M=UI°(€€€€€€€•±¥Ù•ÉåI½±•M½ÕÉ••¥Í¥½¸¹•¥Í¥½¸¹-A}A-°(€€€ôè(€€€€€€€É…¥Í”Y…±¥‘…Ñ¥½¹ÉÉ½È ‰U¹‰•­…¹¹Ñ”ƒq‰•É¹…¡µ••¹ÑÍ¡•¥‘Õ¹œ¸ˆ¤((€€€½±‘}½Ý¹•È€ôÁ…­…”¹Ñ•¡¹¥…±}½Ý¹•È(€€€¹•Ý}½Ý¹•È€ôÁ…­…”¹ÕÍ•}…Í”¹Ñ•¡¹¥…±}½Ý¹•È(€€€‘•¥Í¥½¸€ô•±¥Ù•ÉåI½±•M½ÕÉ••¥Í¥½¸¹½‰©•ÑÌ¹É•…Ñ” (€€€€€€€‘•±¥Ù•Éå}Á…­…”õÁ…­…”°(€€€€€€€É½±•}­•äõ•±¥Ù•ÉåI½±•M½ÕÉ••¥Í¥½¸¹I½±•-•ä¹Q!9%1}=]9H°(€€€€€€€½±‘}Ù…±Õ•}¥õÍÑÈ¡Á…­…”¹Ñ•¡¹¥…±}½Ý¹•É}¥½È€ˆˆ¤°(€€€€€€€½±‘}Ù…±Õ•}±…‰•°õÍÑÈ¡½±‘}½Ý¹•È¤¥˜½±‘}½Ý¹•È•±Í”€‰9¥¡Ð‰•¹…¹¹Ðˆ°(€€€€€€€¹•Ý}Ù…±Õ•}¥õÍÑÈ¡Á…­…”¹ÕÍ•}…Í”¹Ñ•¡¹¥…±}½Ý¹•É}¥½È€ˆˆ¤°(€€€€€€€¹•Ý}Ù…±Õ•}±…‰•°õÍÑÈ¡¹•Ý}½Ý¹•È¤¥˜¹•Ý}½Ý¹•È•±Í”€‰9¥¡Ð‰•¹…¹¹Ðˆ°(€€€€€€€‘•¥Í¥½¸õ…Ñ¥½¸°(€€€€€€€É…Ñ¥½¹…±”õÉ•…Í½¸°(€€€€€€€‘•¥‘•‘}‰äõ…Ñ½È°(€€€€€€€Í½ÕÉ•}ÕÁ‘…Ñ•‘}…ÐõÁ…­…”¹ÕÍ•}…Í”¹ÕÁ‘…Ñ•‘}…Ð°(€€€€¤(€€€¥˜…Ñ¥½¸€ôô•±¥Ù•ÉåI½±•M½ÕÉ••¥Í¥½¸¹•¥Í¥½¸¹=AQ}M=UIè(€€€€€€€Á…­…”¹Ñ•¡¹¥…±}½Ý¹•È€ô¹•Ý}½Ý¹•È(€€€€€€€Á…­…”¹Í…Ù”¡ÕÁ‘…Ñ•}™¥•±‘Ìõl‰Ñ•¡¹¥…±}½Ý¹•Èˆ°€‰ÕÁ‘…Ñ•‘}…Ð‰t¤(€€€€€€€…‘½ÁÑ¥½¸€ô€‰…‘½ÁÑ•ˆ(€€€•±Í”è(€€€€€€€…‘½ÁÑ¥½¸€ô€‰­•ÁÐˆ(€€€É•™É•Í¡}Ñ•¡¹¥…±}½Ý¹•É}Í½ÕÉ•}Í¹…ÁÍ¡½Ð¡Á…­…”°…‘½ÁÑ¥½¸õ…‘½ÁÑ¥½¸¤(€€€É•Í•Ñ}Í•Ñ¥½¹}É•Ù¥•ÝÌ¡Á…­…”°Q!9%1}=]9I}=AQ%=9}IMQ}MQ%=9L¤(€€€É•ÑÕÉ¸‘•¥Í¥½¸(()ÑÉ…¹Í…Ñ¥½¸¹…Ñ½µ¥Œ)‘•˜µ…É­}Á…­…•}É•…‘ä¡Á…­…”è•±¥Ù•ÉåA…­…”¤€´ø9½¹”è(€€€¥˜Á…­…”¹ÍÑ…ÑÕÌ€ôô•±¥Ù•ÉåA…­…”¹MÑ…ÑÕÌ¹!9}=YHè(€€€€€€€É…¥Í”Y…±¥‘…Ñ¥½¹ÉÉ½È ‰¥¸ƒñ‰•É•‰•¹•Ì•±¥Ù•ÉäA…­…”¥ÍÐÕ¹Ù•Ë‘¹‘•É±¥ ¸ˆ¤(€€€™¥¹‘¥¹Ì€ô‰±½­¥¹}™¥¹‘¥¹Ì¡Á…­…”¤(€€€¥˜™¥¹‘¥¹Ìè(€€€€€€€É…¥Í”Y…±¥‘…Ñ¥½¹ÉÉ½È (€€€€€€€€€€€€‰ñÈ‘¥”ƒq‰•É…‰”‰•ÍÑ•¡•¸¹½ 	±½­•Èè€ˆ(€€€€€€€€€€€€¬€ˆð€ˆ¹©½¥¸¡™¥¹‘¥¹œ¹µ•ÍÍ…”™½È™¥¹‘¥¹œ¥¸™¥¹‘¥¹Ì¤(€€€€€€€€¤(€€€Á…­…”¹ÍÑ…ÑÕÌ€ô•±¥Ù•ÉåA…­…”¹MÑ…ÑÕÌ¹Id(€€€Á…­…”¹Í…Ù”¡ÕÁ‘…Ñ•}™¥•±‘Ìõl‰ÍÑ…ÑÕÌˆ°€‰ÕÁ‘…Ñ•‘}…Ð‰t¤(()ÑÉ…¹Í…Ñ¥½¸¹…Ñ½µ¥Œ)‘•˜¡…¹‘}½Ù•É}Á…­…”¡Á…­…”è•±¥Ù•ÉåA…­…”°…Ñ½È¤€´ø9½¹”è(€€€¥˜Á…­…”¹ÍÑ…ÑÕÌ€„ô•±¥Ù•ÉåA…­…”¹MÑ…ÑÕÌ¹Idè(€€€€€€€É…¥Í”Y…±¥‘…Ñ¥½¹ÉÉ½È (€€€€€€€€€€€€‰9ÕÈ•¥¸…±Ì‰•É•¥Ðµ…É­¥•ÉÑ•Ì•±¥Ù•ÉäA…­…”­…¹¸ƒñ‰•É•‰•¸Ý•É‘•¸¸ˆ(€€€€€€€€¤(€€€™¥¹‘¥¹Ì€ô‰±½­¥¹}™¥¹‘¥¹Ì¡Á…­…”¤(€€€¥˜™¥¹‘¥¹Ìè(€€€€€€€É…¥Í”Y…±¥‘…Ñ¥½¹ÉÉ½È (€€€€€€€€€€€€‰¥”I•…‘¥¹•ÍÌµAËñ™Õ¹œ¥ÍÐ¹¥¡Ðµ•¡È•É›ñ±±Ðè€ˆ(€€€€€€€€€€€€¬€ˆð€ˆ¹©½¥¸¡™¥¹‘¥¹œ¹µ•ÍÍ…”™½È™¥¹‘¥¹œ¥¸™¥¹‘¥¹Ì¤(€€€€€€€€¤(€€€Á…­…”¹ÍÑ…ÑÕÌ€ô•±¥Ù•ÉåA…­…”¹MÑ…ÑÕÌ¹!9}=YH(€€€Á…­…”¹¡…¹‘•‘}½Ù•É}‰ä€ô…Ñ½È(€€€Á…­…”¹¡…¹‘•‘}½Ù•É}…Ð€ôÑ¥µ•é½¹”¹¹½Ü ¤(€€€Á…­…”¹Í…Ù”¡ÕÁ‘…Ñ•}™¥•±‘Ìõl‰ÍÑ…ÑÕÌˆ°€‰¡…¹‘•‘}½Ù•É}‰äˆ°€‰¡…¹‘•‘}½Ù•É}…Ðˆ°€‰ÕÁ‘…Ñ•‘}…Ð‰t¤(()}}…±±}|€ôl(€€€€‰AAI=Y}MQQUMLˆ°(€€€€‰‰Õ¥±‘}¥¹¥Ñ¥…±}‘•±¥Ù•Éå}‘…Ñ„ˆ°(€€€€‰É•…Ñ•}‘•±¥Ù•Éå}Á…­…”ˆ°(€€€€‰ÕÉÉ•¹Ñ}‘•±¥Ù•Éå}Á…­…”ˆ°(€€€€‰ÕÉÉ•¹Ñ}¡…¹‘•‘}½Ù•É}Á…­…”ˆ°(€€€€‰‘•±¥Ù•Éå}•±¥¥‰¥±¥Ñäˆ°(€€€€‰‘•±¥Ù•Éå}Í½ÕÉ•}‘¥™™•É•¹•Ìˆ°(€€€€‰¡…¹‘}½Ù•É}Á…­…”ˆ°(€€€€‰±…Ñ•ÍÑ}™¥¹…±}…ÁÁÉ½Ù…°ˆ°(€€€€‰µ…É­}Á…­…•}É•…‘äˆ°(€€€€‰µ¥ÍÍ¥¹}É•…‘å}™¥•±‘Ìˆ°(€€€€‰É•™É•Í¡}Ñ•¡¹¥…±}½Ý¹•É}Í½ÕÉ•}Í¹…ÁÍ¡½Ðˆ°(€€€€‰É•¹‘•É}‘•±¥Ù•Éå}µ…É­‘½Ý¸ˆ°(€€€€‰É•Í•Ñ}Í•Ñ¥½¹}É•Ù¥•ÝÌˆ°(€€€€‰É•Í½±Ù•}Ñ•¡¹¥…±}½Ý¹•É}Í½ÕÉ•}¡…¹”ˆ°(€€€€‰É•Ù¥•Ý}‘•±¥Ù•Éå}Í•Ñ¥½¸ˆ°(€€€€‰Ñ•¡¹¥…±}½Ý¹•É}Í½ÕÉ•}ÍÑ…Ñ”ˆ°)t(