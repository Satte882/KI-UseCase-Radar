import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from ki_radar.accelerator.role_defaults import SUGGESTION, resolve_use_case_business_owner
from ki_radar.accounts.models import User
from ki_radar.accounts.permissions import GROUP_COORDINATOR
from ki_radar.architecture.models import ValueStream
from ki_radar.use_cases.forms import UseCaseForm
from ki_radar.use_cases.role_eligibility import revalidate_use_case_role
from ki_radar.use_cases.services import eligible_second_approvers

pytestmark = pytest.mark.django_db


def _coordinator_user(*, username, business_unit):
    user = User.objects.create_user(
        username=username,
        password="VerySecureTestPassword!123",
        business_unit=business_unit,
    )
    group, _ = Group.objects.get_or_create(name=GROUP_COORDINATOR)
    user.groups.add(group)
    return user


def test_business_owner_selection_reuses_existing_permission_rule(owner, reader):
    assert revalidate_use_case_role(
        role_key="business_owner",
        user=owner,
        required=True,
    ).pk == owner.pk

    with pytest.raises(ValidationError, match="Business Owner"):
        revalidate_use_case_role(
            role_key="business_owner",
            user=reader,
            required=True,
        )


def test_coordinator_selection_reuses_existing_permission_rule(coordinator, reader):
    assert revalidate_use_case_role(role_key="coordinator", user=coordinator).pk == coordinator.pk

    with pytest.raises(ValidationError, match="KI-Koordinator"):
        revalidate_use_case_role(role_key="coordinator", user=reader)


def test_technical_owner_selection_reloads_current_user_state(reader):
    assert revalidate_use_case_role(role_key="technical_owner", user=reader).pk == reader.pk

    User.objects.filter(pk=reader.pk).update(is_active=False)

    with pytest.raises(ValidationError, match="nicht mehr aktiv"):
        revalidate_use_case_role(role_key="technical_owner", user=reader)


def test_cross_role_business_owner_suggestion_is_revalidated_before_use(business_unit, owner):
    value_stream = ValueStream.objects.create(
        name="Beschaffung",
        business_unit=business_unit,
        owner=owner,
        trigger="Bedarf entsteht",
        outcome="Bestellung ist ausgelöst",
        scope_in="Bedarf bis Bestellung",
    )
    resolution = resolve_use_case_business_owner(value_stream=value_stream)
    assert resolution.state == SUGGESTION
    assert resolution.user_id == owner.pk

    owner.groups.clear()

    with pytest.raises(ValidationError, match="Business Owner"):
        revalidate_use_case_role(
            role_key="business_owner",
            user=owner,
            required=True,
        )


def test_use_case_form_applies_role_revalidation(coordinator, reader):
    form = UseCaseForm(current_user=coordinator)
    form.cleaned_data = {"business_owner": reader}

    with pytest.raises(ValidationError, match="Business Owner"):
        form.clean_business_owner()

    form.cleaned_data = {"coordinator": reader}
    with pytest.raises(ValidationError, match="KI-Koordinator"):
        form.clean_coordinator()


def test_optional_roles_may_remain_open():
    assert revalidate_use_case_role(role_key="coordinator", user=None) is None
    assert revalidate_use_case_role(role_key="technical_owner", user=None) is None


def test_unknown_role_fails_closed(reader):
    with pytest.raises(ValidationError, match="Unbekannte"):
        revalidate_use_case_role(role_key="invented_role", user=reader)


def test_second_approver_eligibility_is_recomputed_from_current_state(
    business_unit,
    owner,
    coordinator,
):
    from ki_radar.use_cases.models import UseCase

    use_case = UseCase.objects.create(
        title="AP-4-Testfall",
        problem_statement="Ein reproduzierbarer Testfall benötigt eine klare Rollenprüfung.",
        business_unit=business_unit,
        affected_process="Testprozess",
        business_owner=owner,
        expected_benefit="Weniger manuelle Bearbeitung",
    )
    candidate = _coordinator_user(username="second-reviewer", business_unit=business_unit)

    assert (
        eligible_second_approvers(
            use_case=use_case,
            first_decider=coordinator,
        )
        .filter(pk=candidate.pk)
        .exists()
    )

    User.objects.filter(pk=candidate.pk).update(is_active=False)

    assert not (
        eligible_second_approvers(
            use_case=use_case,
            first_decider=coordinator,
        )
        .filter(pk=candidate.pk)
        .exists()
    )
