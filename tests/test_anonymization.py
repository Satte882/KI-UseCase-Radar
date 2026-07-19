from pathlib import Path
import pytest
from django.test import override_settings
from django.utils import timezone
from ki_radar.accounts.models import PrivacyRequest
from ki_radar.accounts.services import anonymize_user


@pytest.mark.django_db
def test_anonymization_removes_personal_fields(owner, technical_admin, tmp_path):
    owner.first_name = "Max"
    owner.last_name = "Muster"
    owner.email = "max@example.com"
    owner.job_function = "Leitung"
    owner.external_identity_id = "entra-123"
    owner.save()
    request = PrivacyRequest.objects.create(reference="DS-1", subject_user=owner, status=PrivacyRequest.Status.APPROVED, request_received_at=timezone.now())
    ledger = tmp_path / "ledger.jsonl"
    with override_settings(ANONYMIZATION_LEDGER_PATH=ledger):
        anonymize_user(user=owner, privacy_request=request, actor=technical_admin)
    owner.refresh_from_db()
    assert owner.is_anonymized and not owner.is_active
    assert owner.first_name == "" and owner.last_name == ""
    assert owner.email.endswith("@example.invalid")
    assert owner.business_unit is None
    assert Path(ledger).exists()
