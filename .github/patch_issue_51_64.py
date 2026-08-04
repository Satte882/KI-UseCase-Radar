from pathlib import Path
import re

blockers = Path("tests/test_actionable_blockers.py")
text = blockers.read_text(encoding="utf-8")
text = text.replace(
    '    assert "Zum ersten offenen Punkt" in detail_content\n',
    '    assert detail_content.count(\'data-testid="primary-next-action-control"\') == 1\n',
)
blockers.write_text(text, encoding="utf-8")

solution_tests = Path("tests/test_issue_58_solution_next_action.py")
text = solution_tests.read_text(encoding="utf-8")
text = text.replace(
    '    assert "Erste Lösungsoption ergänzen" in content\n'
    '    assert "Erste Option ergänzen" in content\n'
    '    assert "Weitere Option ergänzen" not in content\n',
    '    assert content.count("Erste Lösungsoption ergänzen") == 1\n'
    '    assert "Erste Option ergänzen" not in content\n'
    '    assert "Weitere Option ergänzen" not in content\n',
)
solution_tests.write_text(text, encoding="utf-8")

process_template = Path("templates/architecture/process_analysis_detail.html")
text = process_template.read_text(encoding="utf-8")
old = """        {% if can_create_use_case and process_analysis.stage.value_stream.focus.is_selected and option.recommendation == 'preferred' and option.starts_ai_use_case and journey.next_action.key == 'use_case' %}<a class=\"btn btn-sm btn-primary w-100 mt-2\" href=\"{{ journey.next_action.url }}\" data-testid=\"primary-next-action-control\">{{ journey.next_action.action_label|default:\"Bevorzugte Option als Use Case prüfen\" }} →</a>{% endif %}\n"""
new = """        {% if can_create_use_case and process_analysis.stage.value_stream.focus.is_selected and option.recommendation == 'preferred' and option.starts_ai_use_case %}\n        {% if journey.next_action.key == 'use_case' %}<a class=\"btn btn-sm btn-primary w-100 mt-2\" href=\"{{ journey.next_action.url }}\" data-testid=\"primary-next-action-control\">{{ journey.next_action.action_label|default:\"Bevorzugte Option als Use Case prüfen\" }} →</a>\n        {% else %}<a class=\"btn btn-sm btn-outline-secondary w-100 mt-2\" href=\"{% url 'architecture:solution_option_start_use_case' option.pk %}\">Bevorzugte Option als Use Case prüfen</a>{% endif %}\n        {% endif %}\n"""
if old not in text:
    raise SystemExit("Process template target not found")
process_template.write_text(text.replace(old, new), encoding="utf-8")

delivery_tests = Path("tests/test_delivery_handover.py")
text = delivery_tests.read_text(encoding="utf-8")
text = text.replace("from django.template.loader import render_to_string\n", "")
text = text.replace("from django.test import RequestFactory\n", "")
text = text.replace("from ki_radar.use_cases.workflow import build_use_case_journey\n", "")

creation = '''@pytest.mark.django_db
def test_use_case_detail_renders_delivery_package_creation_as_post_form(
    client,
    owner,
    coordinator,
    business_unit,
):
    use_case = make_use_case(owner, business_unit)
    approve_use_case(use_case, coordinator)
    create_url = reverse("delivery:package_create", kwargs={"use_case_id": use_case.pk})
    client.force_login(coordinator)

    response = client.get(use_case.get_absolute_url())
    rendered = response.content.decode()

    assert response.status_code == 200
    assert f'<form method="post" action="{create_url}">' in rendered
    assert 'name="csrfmiddlewaretoken"' in rendered
    assert "Delivery Package erzeugen" in rendered
    assert f'href="{create_url}"' not in rendered
    assert rendered.count('data-testid="primary-next-action-control"') == 1


'''
text, count = re.subn(
    r"@pytest\.mark\.django_db\ndef test_topbar_renders_delivery_package_creation_as_post_form\(.*?(?=@pytest\.mark\.django_db\ndef test_topbar_marks_ready_delivery_package_via_post)",
    creation,
    text,
    flags=re.S,
)
if count != 1:
    raise SystemExit(f"Creation test replacement count: {count}")

ready = '''@pytest.mark.django_db
def test_delivery_detail_marks_ready_package_via_post(
    client,
    owner,
    coordinator,
    business_unit,
):
    use_case = make_use_case(owner, business_unit)
    approve_use_case(use_case, coordinator)
    package = create_delivery_package(use_case=use_case, actor=coordinator)
    complete_delivery_readiness(package)
    ready_url = reverse("delivery:package_mark_ready", kwargs={"pk": package.pk})
    client.force_login(coordinator)

    detail = client.get(package.get_absolute_url())
    rendered = detail.content.decode()

    assert detail.status_code == 200
    assert f'<form method="post" action="{ready_url}">' in rendered
    assert 'name="csrfmiddlewaretoken"' in rendered
    assert "Als bereit markieren" in rendered
    assert f'href="{ready_url}"' not in rendered

    response = client.post(ready_url)
    package.refresh_from_db()

    assert response.status_code == 302
    assert response.url == package.get_absolute_url()
    assert package.status == DeliveryPackage.Status.READY


'''
text, count = re.subn(
    r"@pytest\.mark\.django_db\ndef test_topbar_marks_ready_delivery_package_via_post\(.*?(?=@pytest\.mark\.django_db\ndef test_topbar_hands_over_ready_delivery_package_via_post)",
    ready,
    text,
    flags=re.S,
)
if count != 1:
    raise SystemExit(f"Ready test replacement count: {count}")

handover = '''@pytest.mark.django_db
def test_delivery_detail_hands_over_ready_package_via_post(
    client,
    owner,
    coordinator,
    business_unit,
):
    use_case = make_use_case(owner, business_unit)
    approve_use_case(use_case, coordinator)
    package = create_delivery_package(use_case=use_case, actor=coordinator)
    complete_delivery_readiness(package)
    mark_package_ready(package)
    handover_url = reverse("delivery:package_handover", kwargs={"pk": package.pk})
    client.force_login(coordinator)

    detail = client.get(package.get_absolute_url())
    rendered = detail.content.decode()

    assert detail.status_code == 200
    assert f'<form method="post" action="{handover_url}">' in rendered
    assert 'name="csrfmiddlewaretoken"' in rendered
    assert "An Delivery übergeben" in rendered
    assert f'href="{handover_url}"' not in rendered

    response = client.post(handover_url)
    package.refresh_from_db()

    assert response.status_code == 302
    assert response.url == package.get_absolute_url()
    assert package.status == DeliveryPackage.Status.HANDED_OVER
    assert package.handed_over_by == coordinator


'''
text, count = re.subn(
    r"@pytest\.mark\.django_db\ndef test_topbar_hands_over_ready_delivery_package_via_post\(.*?(?=@pytest\.mark\.django_db\ndef test_delivery_overview_is_visible_and_creation_is_coordinator_only)",
    handover,
    text,
    flags=re.S,
)
if count != 1:
    raise SystemExit(f"Handover test replacement count: {count}")
delivery_tests.write_text(text, encoding="utf-8")
