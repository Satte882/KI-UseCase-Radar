from pathlib import Path

# The process edit view correctly requires an approved Deep-Dive focus.
test_path = Path("tests/test_process_validation.py")
text = test_path.read_text(encoding="utf-8")
text = text.replace(
    "from ki_radar.architecture.forms import ProcessAnalysisForm\n",
    "from ki_radar.architecture.focus import ValueStreamFocus\n"
    "from ki_radar.architecture.forms import ProcessAnalysisForm\n",
    1,
)
text = text.replace(
    "from ki_radar.architecture.models import (\n",
    "from ki_radar.architecture.models import (\n",
    1,
)
text = text.replace(
    ")\n\n\ndef make_process(owner, business_unit):\n",
    ")\nfrom ki_radar.core.taxonomy import BusinessDomain, ScreeningLevel\n\n\ndef make_process(owner, business_unit):\n",
    1,
)
anchor = '''    stage = ValueStreamStage.objects.create(\n        value_stream=stream, sequence=1, name="Prüfen"\n    )\n'''
replacement = '''    ValueStreamFocus.objects.create(\n        value_stream=stream,\n        business_domain=BusinessDomain.OTHER,\n        capability="Anfragen prüfen",\n        strategic_impact=ScreeningLevel.MEDIUM,\n        economic_potential=ScreeningLevel.MEDIUM,\n        pain_intensity=ScreeningLevel.MEDIUM,\n        data_accessibility=ScreeningLevel.MEDIUM,\n        change_effort=ScreeningLevel.MEDIUM,\n        status=ValueStreamFocus.Status.SELECTED,\n        rationale="Für den Deep Dive ausgewählt.",\n        updated_by=owner,\n    )\n    stage = ValueStreamStage.objects.create(\n        value_stream=stream, sequence=1, name="Prüfen"\n    )\n'''
if anchor not in text:
    raise RuntimeError("Process validation test setup anchor not found")
test_path.write_text(text.replace(anchor, replacement, 1), encoding="utf-8")

# Opt into Django's future HTTPS default for the newly introduced URL field.
form_path = Path("ki_radar/architecture/forms.py")
form_text = form_path.read_text(encoding="utf-8")
old = '''    evidence_url = forms.URLField(\n        required=False,\n        label="Nachweis",\n'''
new = '''    evidence_url = forms.URLField(\n        required=False,\n        assume_scheme="https",\n        label="Nachweis",\n'''
if old not in form_text:
    raise RuntimeError("Process validation URL field anchor not found")
form_path.write_text(form_text.replace(old, new, 1), encoding="utf-8")
