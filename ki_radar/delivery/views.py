from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ki_radar.use_cases.models import UseCase

from .forms import DeliveryPackageForm
from .models import DeliveryPackage
from .permissions import (
    can_create_package,
    can_edit_package,
    can_transition_package,
    can_view_package,
)
from .services import (
    APPROVED_STATUSES,
    create_delivery_package,
    hand_over_package,
    mark_package_ready,
    missing_ready_fields,
    render_delivery_markdown,
)


@login_required
def package_list(request):
    use_cases = list(
        UseCase.objects.filter(
            is_archived=False,
            decision_status__in=APPROVED_STATUSES,
        )
        .select_related("business_unit", "business_owner")
        .prefetch_related("delivery_packages", "approval_decisions")
        .order_by("business_unit__name", "short_id")
    )
    rows = []
    for use_case in use_cases:
        decisions = list(use_case.approval_decisions.all())
        final_decision = next(
            (
                decision
                for decision in decisions
                if decision.decision_status in APPROVED_STATUSES
                and decision.finalized_at is not None
            ),
            None,
        )
        packages = list(use_case.delivery_packages.all())
        rows.append(
            {
                "use_case": use_case,
                "eligible": final_decision is not None,
                "eligibility_reason": (
                    "" if final_decision else "Die positive Freigabe ist noch nicht final dokumentiert."
                ),
                "latest_package": packages[0] if packages else None,
            }
        )
    return render(
        request,
        "delivery/package_list.html",
        {"rows": rows, "can_create": can_create_package(request.user)},
    )


@login_required
@require_POST
def package_create(request, use_case_id):
    if not can_create_package(request.user):
        raise PermissionDenied
    use_case = get_object_or_404(
        UseCase.objects.select_related("business_unit", "business_owner").prefetch_related(
            "approval_decisions__assessment",
            "delivery_packages",
        ),
        pk=use_case_id,
    )
    try:
        package = create_delivery_package(use_case=use_case, actor=request.user)
    except ValidationError as exc:
        messages.error(request, str(exc))
        return redirect("delivery:package_list")
    messages.success(
        request,
        f"Delivery Package v{package.version} wurde aus der finalen Freigabe erzeugt.",
    )
    return redirect(package)


@login_required
def package_detail(request, pk):
    package = get_object_or_404(
        DeliveryPackage.objects.select_related(
            "use_case__business_unit",
            "use_case__business_owner",
            "generated_from_decision__assessment",
            "created_by",
            "handed_over_by",
        ),
        pk=pk,
    )
    if not can_view_package(request.user, package):
        raise PermissionDenied
    return render(
        request,
        "delivery/package_detail.html",
        {
            "package": package,
            "can_edit": can_edit_package(request.user, package),
            "can_transition": can_transition_package(request.user),
            "missing_ready_fields": missing_ready_fields(package),
        },
    )


@login_required
def package_update(request, pk):
    package = get_object_or_404(
        DeliveryPackage.objects.select_related("use_case"),
        pk=pk,
    )
    if not can_edit_package(request.user, package):
        raise PermissionDenied
    form = DeliveryPackageForm(request.POST or None, instance=package)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Delivery Package wurde aktualisiert.")
        return redirect(package)
    return render(
        request,
        "delivery/package_form.html",
        {"form": form, "package": package},
    )


@login_required
@require_POST
def package_mark_ready(request, pk):
    package = get_object_or_404(DeliveryPackage, pk=pk)
    if not can_transition_package(request.user):
        raise PermissionDenied
    try:
        mark_package_ready(package)
    except ValidationError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Delivery Package ist bereit zur Übergabe.")
    return redirect(package)


@login_required
@require_POST
def package_handover(request, pk):
    package = get_object_or_404(DeliveryPackage, pk=pk)
    if not can_transition_package(request.user):
        raise PermissionDenied
    try:
        hand_over_package(package, request.user)
    except ValidationError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Delivery Package wurde verbindlich übergeben.")
    return redirect(package)


@login_required
def package_export_markdown(request, pk):
    package = get_object_or_404(
        DeliveryPackage.objects.select_related("use_case"),
        pk=pk,
    )
    if not can_view_package(request.user, package):
        raise PermissionDenied
    response = HttpResponse(
        render_delivery_markdown(package),
        content_type="text/markdown; charset=utf-8",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{package.use_case.short_id}-delivery-v{package.version}.md"'
    )
    return response
