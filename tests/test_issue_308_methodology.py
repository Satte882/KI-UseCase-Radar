import pytest
from django.urls import reverse

from ki_radar.accelerator.catalogs import get_capture_catalog
from ki_radar.accelerator.forms import CaptureSectionForm
from ki_radar.accelerator.models import CaptureSession
from ki_radar.accelerator.views import METHODOLOGY_DOWNLOAD_NAME, METHODOLOGY_PATH


@pytest.mark.django_db
def test_value_stream_methodology_modal_is_available(client, owner):
    client.force_login(owner)
    session = CaptureSession.objects.create(
        owner=owner,
        capture_type=CaptureSession.CaptureType.VALUE_STREAM,
        catalog_version="1.0",
        schema_version="1.0",
    )

    response = client.get(
        reverse(
            "accelerator:capture_step",
            kwargs={"session_id": session.pk, "step": 1},
        )
    )
    body = response.content.decode()

    assert response.status_code == 200
    assert "value-stream-methodology-modal" in body
    assert "Methodik &amp; Beispiel" in body
    assert "Entwurf prüfen" in body


@pytest.mark.django_db
def test_methodology_download_serves_canonical_repository_markdown(client, owner):
    client.force_login(owner)

    response = client.get(reverse("accelerator:value_stream_methodology_download"))

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/markdown")
    assert METHODOLOGY_DOWNLOAD_NAME in response["Content-Disposition"]
    assert response.content.decode() == METHODOLOGY_PATH.read_text(encoding="utf-8")
    assert "**Version:** 1.2" in response.content.decode()


@pytest.mark.django_db
def test_methodology_download_requires_login(client):
    response = client.get(reverse("accelerator:value_stream_methodology_download"))

    assert response.status_code == 302
    assert "/login/" in response.url


def test_guided_stage_capture_explains_value_progress_without_new_capture_fields():
    catalog = get_capture_catalog(CaptureSession.CaptureType.VALUE_STREAM)
    stage_section = next(section for section in catalog.sections if section.key == "stages")
    form = CaptureSectionForm(section=stage_section)

    assert "stages" in form.fields
    assert "Wertfortschritt" in stage_section.help_text
    assert "Was liegt vorher vor?" in stage_section.help_text
    assert "Was verändert sich fachlich?" in stage_section.help_text
    assert "welcher relevante Zustand" in stage_section.help_text
