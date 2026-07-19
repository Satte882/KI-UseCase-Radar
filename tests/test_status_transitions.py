from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from ki_radar.governance.models import GovernanceAssessment
from ki_radar.use_cases.models import UseCase
from ki_radar.use_cases.services import apply_status_transition


@pytest.fixture
def use_case(owner, business_unit):
    return UseCase.objects.create(
        title="Assistent",
        problem_statement="Wissen ist verteilt",
        business_unit=business_unit,
        affected_process="Auskunft",
        business_owner=owner,
        expected_benefit="Schnellere Antworten",
    )


@pytest.mark.django_db
def test_transition_to_pilot_requires_fields_and_governance(use_case, coordinator):
    with pytest.raises(ValidationError):
        apply_status_transition(
            use_case=use_case, target_status=UseCase.Status.PILOT, actor=coordinator
        )


@pytest.mark.django_db
def test_transition_to_pilot_succeeds(use_case, coordinator):
    use_case.data_sources = "Wissensbasis"
    use_case.next_review_date = timezone.localdate()
    use_case.planned_pilot_end = timezone.localdate()
    use_case.metric_name = "Antwortzeit"
    use_case.metric_type = UseCase.MetricType.DURATION
    use_case.metric_direction = UseCase.MetricDirection.LOWER
    use_case.metric_unit = "Minuten"
    use_case.metric_baseline = Decimal("30")
    use_case.metric_target = Decimal("10")
    use_case.metric_measurement_method = "Zeitmessung bei 20 repräsentativen Anfragen"
    use_case.save()
    GovernanceAssessment.objects.create(
        use_case=use_case,
        assessment_date=timezone.localdate(),
        reviewer=coordinator,
        basis_version="2026-01",
        result=GovernanceAssessment.Result.NO_FLAGS,
        rationale="Keine Hinweise",
    )
    apply_status_transition(
        use_case=use_case, target_status=UseCase.Status.PILOT, actor=coordinator
    )
    use_case.refresh_from_db()
    assert use_case.status == UseCase.Status.PILOT
