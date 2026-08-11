from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
PORTFOLIO = (ROOT / "templates" / "reporting" / "portfolio.html").read_text(encoding="utf-8")
USE_CASE_DETAIL = (ROOT / "templates" / "use_cases" / "detail.html").read_text(encoding="utf-8")
MIGRATION = (ROOT / "docs" / "UI_CONTROL_ROOM_MIGRATION.md").read_text(encoding="utf-8")


def test_existing_body_class_block_is_the_page_level_migration_hook():
    assert '<body class="ui-vnext {% block body_class %}{% endblock %}">' in BASE
    assert "ui-control-room" not in PORTFOLIO
    assert "ui-control-room" not in USE_CASE_DETAIL


def test_migration_contract_keeps_control_room_rules_page_scoped():
    assert "`body_class`" in MIGRATION
    assert "{% block body_class %}ui-control-room{% endblock %}" in MIGRATION
    assert "unter `.ui-control-room` gescoped" in MIGRATION
    assert "keine Runtime-Feature-Flags" in MIGRATION
    assert "temporär" in MIGRATION


def test_migration_contract_contains_reference_pages_and_acceptance_gates():
    assert "`templates/reporting/portfolio.html`" in MIGRATION
    assert "`templates/use_cases/detail.html`" in MIGRATION
    assert "Gate A" in MIGRATION
    assert "Gate B" in MIGRATION
    assert "Final Gate" in MIGRATION
    assert "Kein Merge auf `main` vor expliziter Freigabe" in MIGRATION


def test_migration_contract_records_ci_batch_fix_rule():
    assert "komplette Lauf abgewartet" in MIGRATION
    assert "alle fehlgeschlagenen Jobs und deren Logs vollständig geprüft" in MIGRATION
    assert "Sammel-Fix-Commit" in MIGRATION
    assert "Folge-Jobs blockiert" in MIGRATION
