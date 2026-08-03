from pathlib import Path

path = Path("tests/test_value_stream_scope.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    "from ki_radar.architecture.forms import ValueStreamForm\n",
    "from ki_radar.architecture.focus import ValueStreamFocus\n"
    "from ki_radar.architecture.forms import ValueStreamForm\n",
    1,
)
text = text.replace(
    "from ki_radar.architecture.models import ValueStream, ValueStreamStage\n",
    "from ki_radar.architecture.models import ValueStream, ValueStreamStage\n"
    "from ki_radar.core.taxonomy import BusinessDomain, ScreeningLevel\n",
    1,
)
old = '''    stage = ValueStreamStage.objects.create(\n        value_stream=value_stream, sequence=1, name="Prüfen"\n    )\n    client.force_login(owner)\n\n    response = client.get(reverse("architecture:process_analysis_create", args=[stage.pk]))\n\n    content = response.content.decode()\n    assert response.status_code == 302  # Fokusentscheidung ist weiterhin das vorgelagerte Gate.\n    assert not hasattr(stage, "scope_in")\n    assert stage.value_stream.scope_in == "Prüfung und Entscheidung"\n    assert stage.value_stream.scope_out == "Operative Ausführung"\n'''
new = '''    ValueStreamFocus.objects.create(\n        value_stream=value_stream,\n        business_domain=BusinessDomain.OTHER,\n        capability="Anfragen bearbeiten",\n        strategic_impact=ScreeningLevel.MEDIUM,\n        economic_potential=ScreeningLevel.MEDIUM,\n        pain_intensity=ScreeningLevel.MEDIUM,\n        data_accessibility=ScreeningLevel.MEDIUM,\n        change_effort=ScreeningLevel.MEDIUM,\n        status=ValueStreamFocus.Status.SELECTED,\n        rationale="Für den Deep Dive ausgewählt.",\n        updated_by=owner,\n    )\n    value_stream.status = ValueStream.Status.ACTIVE\n    value_stream.save(update_fields=["status", "updated_at"])\n    stage = ValueStreamStage.objects.create(\n        value_stream=value_stream, sequence=1, name="Prüfen"\n    )\n    client.force_login(owner)\n\n    response = client.get(reverse("architecture:process_analysis_create", args=[stage.pk]))\n\n    content = response.content.decode()\n    assert response.status_code == 200\n    assert "Quellkontext aus dem Value Stream" in content\n    assert "Prüfung und Entscheidung" in content\n    assert "Operative Ausführung" in content\n    assert not hasattr(stage, "scope_in")\n'''
if old not in text:
    raise RuntimeError("Expected issue #57 test block not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
