from __future__ import annotations

from django import template
from django.urls import reverse

register = template.Library()

WORKFLOW = (
    ("discovery", "Discovery", ("value_stream",)),
    ("focus", "Fokus & Priorisierung", ("focus",)),
    ("use_cases", "Use Cases", ("process", "solution", "use_case")),
    ("assessment", "Bewertung", ("assessment",)),
    ("approval", "Freigabe", ("approval",)),
    ("delivery", "Delivery", ("delivery",)),
)


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


def _route_states(request):
    resolver = request.resolver_match
    namespace = resolver.namespace if resolver else ""
    url_name = resolver.url_name if resolver else ""
    states = {key: "context" for key, _label, _keys in WORKFLOW}

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
    elif namespace == "reviews" or (
        namespace == "reporting" and url_name == "dashboard"
    ):
        states.update(
            discovery="optional",
            focus="optional",
            use_cases="complete",
            assessment="complete",
            approval="current",
            delivery="upcoming",
        )
    return states


@register.simple_tag
def workflow_steps(journey, request):
    links = {
        "discovery": reverse("architecture:value_stream_list"),
        "focus": reverse("architecture:value_stream_list"),
        "use_cases": reverse("use_cases:list"),
        "assessment": reverse("reporting:portfolio"),
        "approval": reverse("reporting:dashboard"),
        "delivery": reverse("delivery:package_list"),
    }
    route_states = _route_states(request)
    raw_steps = journey.steps if journey else ()
    result = []
    for key, label, raw_keys in WORKFLOW:
        result.append(
            {
                "key": key,
                "label": label,
                "state": _aggregate_state(raw_steps, raw_keys) if journey else route_states[key],
                "url": links[key],
            }
        )
    return result


@register.filter
def local_step_group(step_key):
    if step_key in {"value_stream", "focus", "process", "solution"}:
        return "analysis"
    if step_key in {"use_case", "assessment", "approval", "delivery"}:
        return "initiative"
    return ""
