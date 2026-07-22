from __future__ import annotations

from urllib.parse import urlencode

from django import template
from django.urls import reverse

register = template.Library()

SELECTION_WORKFLOW = (
    ("discovery", "Discovery", ("value_stream",)),
    ("focus", "Fokus & Priorisierung", ("focus",)),
    ("use_cases", "Use Cases", ("process", "solution", "use_case")),
    ("assessment", "Bewertung", ("assessment",)),
    ("approval", "Freigabe", ("approval",)),
    ("delivery", "Delivery", ("delivery",)),
)
OUTCOME_WORKFLOW = (
    ("handover", "Übergabe", ("handover",)),
    ("pilot", "Pilot", ("pilot",)),
    ("measurement", "Wirkung", ("measurement",)),
    ("outcome_decision", "Ergebnisentscheidung", ("outcome_decision",)),
    ("operation", "Betrieb", ("operation",)),
    ("closure", "Abschluss", ("closure",)),
)
WORKFLOW = SELECTION_WORKFLOW
OUTCOME_STEP_KEYS = {key for key, _label, _raw_keys in OUTCOME_WORKFLOW}


def _aggregate_state(raw_steps, keys):
    states = [step.state for step in raw_steps if step.key in keys]
    if not states:
        return "optional"
    if "blocked" in states:
        return "blocked"
    if "current" in states:
        return "current"
    if all(state == "optional" for state in states):
        return "optional"
    if "upcoming" in states:
        return "upcoming"
    if "complete" in states:
        return "complete"
    return "upcoming"


def _is_outcome_workspace(journey, request):
    resolver = request.resolver_match
    is_outcome_route = bool(
        resolver and resolver.namespace == "reporting" and resolver.url_name == "outcome_workspace"
    )
    has_outcome_steps = bool(
        journey and any(step.key in OUTCOME_STEP_KEYS for step in journey.steps)
    )
    return is_outcome_route or has_outcome_steps


def _workflow_definition(journey, request):
    if not _is_outcome_workspace(journey, request):
        return [(*definition, False) for definition in SELECTION_WORKFLOW]
    return [(*definition, False) for definition in OUTCOME_WORKFLOW]


def _selection_route_states(request):
    resolver = request.resolver_match
    namespace = resolver.namespace if resolver else ""
    url_name = resolver.url_name if resolver else ""
    states = {key: "context" for key, _label, _keys in SELECTION_WORKFLOW}

    if namespace == "architecture":
        states["discovery"] = "current"
        states["focus"] = "upcoming"
        states["use_cases"] = "upcoming"
    elif namespace == "use_cases" and url_name == "assessment_create":
        states.update(
            discovery="optional",
            focus="optional",
            use_cases="complete",
            assessment="current",
            approval="upcoming",
            delivery="upcoming",
        )
    elif namespace == "use_cases" and url_name == "approval_decision_create":
        states.update(
            discovery="optional",
            focus="optional",
            use_cases="complete",
            assessment="complete",
            approval="current",
            delivery="upcoming",
        )
    elif namespace == "use_cases":
        states.update(
            discovery="optional",
            focus="optional",
            use_cases="current",
            assessment="upcoming",
            approval="upcoming",
            delivery="upcoming",
        )
    elif namespace == "delivery":
        states.update(
            discovery="optional",
            focus="optional",
            use_cases="complete",
            assessment="complete",
            approval="complete",
            delivery="current",
        )
    elif namespace == "reviews" or (namespace == "reporting" and url_name == "dashboard"):
        states.update(
            discovery="optional",
            focus="optional",
            use_cases="complete",
            assessment="complete",
            approval="current",
            delivery="upcoming",
        )
    return states


def _outcome_route_states(request):
    current_stage = request.GET.get("stage", "pilot")
    stage_to_step = {
        "pilot": "pilot",
        "effect": "measurement",
        "decision": "outcome_decision",
        "operation": "operation",
        "closure": "closure",
    }
    current_step = stage_to_step.get(current_stage, "pilot")
    states = {key: "upcoming" for key, _label, _keys in OUTCOME_WORKFLOW}
    states["handover"] = "context"
    states[current_step] = "current"
    return states


def _outcome_link(request, stage):
    query = {"stage": stage}
    if request.GET.get("use_case"):
        query["use_case"] = request.GET["use_case"]
    return f"{reverse('reporting:outcome_workspace')}?{urlencode(query)}"


def _links(request):
    return {
        "discovery": reverse("architecture:value_stream_list"),
        "focus": reverse("architecture:value_stream_list"),
        "use_cases": reverse("use_cases:list"),
        "assessment": reverse("reporting:portfolio"),
        "approval": reverse("reporting:dashboard"),
        "delivery": reverse("delivery:package_list"),
        "handover": _outcome_link(request, "pilot"),
        "pilot": _outcome_link(request, "pilot"),
        "measurement": _outcome_link(request, "effect"),
        "outcome_decision": _outcome_link(request, "decision"),
        "operation": _outcome_link(request, "operation"),
        "closure": _outcome_link(request, "closure"),
    }


@register.simple_tag
def workflow_steps(journey, request):
    definitions = _workflow_definition(journey, request)
    links = _links(request)
    raw_steps = journey.steps if journey else ()
    selection_states = _selection_route_states(request)
    outcome_states = _outcome_route_states(request)
    result = []
    for key, label, raw_keys, divider_before in definitions:
        if journey:
            state = _aggregate_state(raw_steps, raw_keys)
        elif key in selection_states:
            state = selection_states[key]
        else:
            state = outcome_states[key]
        result.append(
            {
                "key": key,
                "label": label,
                "state": state,
                "url": links[key],
                "divider_before": divider_before,
            }
        )
    return result


@register.filter
def local_step_group(step_key):
    if step_key in {"value_stream", "focus", "process", "solution"}:
        return "analysis"
    if step_key in {"use_case", "assessment", "approval", "delivery"}:
        return "initiative"
    if step_key in OUTCOME_STEP_KEYS:
        return "outcome"
    return ""
