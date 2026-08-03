from pathlib import Path


def replace(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected block not found in {path}: {old[:120]!r}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


# permissions.py: only technical admins/superusers may use the same-person override.
replace(
    "ki_radar/delivery/permissions.py",
    "from ki_radar.accounts.permissions import (\n    GROUP_BUSINESS_OWNER,\n    GROUP_COORDINATOR,\n    in_group,\n    is_coordinator,\n)",
    "from ki_radar.accounts.permissions import (\n    GROUP_BUSINESS_OWNER,\n    GROUP_COORDINATOR,\n    in_group,\n    is_coordinator,\n    is_technical_admin,\n)",
)
replace(
    "ki_radar/delivery/permissions.py",
    '''def confirmation_role_label(role: str, *, assigned: bool) -> str:\n    if role == "business":\n        return "Business Owner" if assigned else "Berechtigte fachliche Stellvertretung"\n    return "Technical Owner" if assigned else "Berechtigte technische Stellvertretung"\n\n\ndef can_independently_check(\n    user,\n    package: DeliveryPackage,\n    review: DeliverySectionReview,\n) -> bool:\n    if not review.has_role_collapse or review.business_confirmed_by_id == user.id:\n        return False\n    return bool(reviewer_roles(user, package, review.section_key))\n''',
    '''def can_use_admin_confirmation_override(user) -> bool:\n    return is_technical_admin(user)\n\n\ndef confirmation_role_label(\n    role: str,\n    *,\n    assigned: bool,\n    admin_override: bool = False,\n) -> str:\n    if admin_override:\n        return "Admin-Sonderbestätigung"\n    if role == "business":\n        return "Business Owner" if assigned else "Berechtigte fachliche Stellvertretung"\n    return "Technical Owner" if assigned else "Berechtigte technische Stellvertretung"\n''',
)
replace(
    "ki_radar/delivery/permissions.py",
    "from .models import DeliveryPackage, DeliverySectionReview\n",
    "from .models import DeliveryPackage\n",
)

# models.py: retain a compact, explicit audit marker; remove the abandoned generic collapse review.
replace(
    "ki_radar/delivery/models.py",
    '''    role_collapse_reason = models.TextField(blank=True)\n    independent_checked_by = models.ForeignKey(\n        settings.AUTH_USER_MODEL,\n        null=True,\n        blank=True,\n        on_delete=models.SET_NULL,\n        related_name="independently_checked_delivery_sections",\n    )\n    independent_checked_at = models.DateTimeField(null=True, blank=True)\n    independent_check_role = models.CharField(max_length=120, blank=True)\n    independent_check_note = models.TextField(blank=True)\n''',
    '''    role_collapse_reason = models.TextField(blank=True)\n    admin_override_confirmed = models.BooleanField(default=False)\n''',
)
replace(
    "ki_radar/delivery/models.py",
    '''    @property\n    def independent_control_complete(self) -> bool:\n        return not self.has_role_collapse or self.independent_checked_at is not None\n\n    @property\n    def confirmations_complete(self) -> bool:\n        return self.role_confirmations_complete and self.independent_control_complete\n''',
    '''    @property\n    def confirmations_complete(self) -> bool:\n        return self.role_confirmations_complete\n''',
)

# Migration is not merged yet, so keep it aligned with the final model rather than creating follow-up debt.
path = Path("ki_radar/delivery/migrations/0004_delivery_confirmation_audit.py")
text = path.read_text(encoding="utf-8")
start = text.index("        migrations.AddField(\n            model_name=\"deliverysectionreview\",\n            name=\"independent_checked_by\"")
end = text.index("    ]\n", start)
replacement = '''        migrations.AddField(\n            model_name="deliverysectionreview",\n            name="admin_override_confirmed",\n            field=models.BooleanField(default=False),\n        ),\n'''
text = text[:start] + replacement + text[end:]
text = text.replace("import django.db.models.deletion\n", "")
text = text.replace("from django.conf import settings\n", "")
text = text.replace("        migrations.swappable_dependency(settings.AUTH_USER_MODEL),\n", "")
path.write_text(text, encoding="utf-8")

# services.py: same person is rejected except for an audited technical-admin override.
replace(
    "ki_radar/delivery/services.py",
    "from .permissions import confirmation_role_label, reviewer_roles\n",
    "from .permissions import (\n    can_use_admin_confirmation_override,\n    confirmation_role_label,\n    reviewer_roles,\n)\n",
)
replace(
    "ki_radar/delivery/services.py",
    '''        role_collapse_reason="",\n        independent_checked_by=None,\n        independent_checked_at=None,\n        independent_check_role="",\n        independent_check_note="",\n''',
    '''        role_collapse_reason="",\n        admin_override_confirmed=False,\n''',
)
replace(
    "ki_radar/delivery/services.py",
    '''        if other_actor_id == actor.id:\n            dual_owner = bool(\n                package.use_case.business_owner_id == actor.id\n                and package.use_case.technical_owner_id == actor.id\n            )\n            if not dual_owner:\n                raise ValidationError(\n                    "Dieselbe Person darf beide Rollen nur bei ausdrücklich zugewiesenem "\n                    "Business- und Technical-Owner-Rollenkollaps bestätigen."\n                )\n            collapse_reason = role_collapse_reason.strip()\n            if not collapse_reason:\n                raise ValidationError(\n                    "Für die zusammengeführte Rollenbestätigung ist eine Begründung erforderlich."\n                )\n            review.role_collapse_reason = collapse_reason\n        else:\n            review.role_collapse_reason = ""\n''',
    '''        if other_actor_id == actor.id:\n            if not can_use_admin_confirmation_override(actor):\n                raise ValidationError(\n                    "Dieselbe Person darf fachlich und technisch nur als Technischer "\n                    "Administrator für Admin- oder Testzwecke bestätigen."\n                )\n            collapse_reason = role_collapse_reason.strip()\n            if not collapse_reason:\n                raise ValidationError(\n                    "Für die Admin-Sonderbestätigung ist eine Begründung erforderlich."\n                )\n            review.role_collapse_reason = collapse_reason\n            review.admin_override_confirmed = True\n        else:\n            review.role_collapse_reason = ""\n            review.admin_override_confirmed = False\n''',
)
replace(
    "ki_radar/delivery/services.py",
    '''        setattr(\n            review,\n            f"{role}_confirmation_role",\n            confirmation_role_label(role, assigned=assigned_owner_id == actor.id),\n        )\n        review.independent_checked_by = None\n        review.independent_checked_at = None\n        review.independent_check_role = ""\n        review.independent_check_note = ""\n        review.review_status = (\n''',
    '''        setattr(\n            review,\n            f"{role}_confirmation_role",\n            confirmation_role_label(\n                role,\n                assigned=assigned_owner_id == actor.id,\n                admin_override=review.admin_override_confirmed,\n            ),\n        )\n        if review.admin_override_confirmed:\n            review.business_confirmation_role = "Admin-Sonderbestätigung"\n            review.technical_confirmation_role = "Admin-Sonderbestätigung"\n        review.review_status = (\n''',
)
start_marker = '    elif action == "independent_check":\n'
end_marker = '    elif action == "block":\n'
path = Path("ki_radar/delivery/services.py")
text = path.read_text(encoding="utf-8")
start = text.index(start_marker)
end = text.index(end_marker, start)
text = text[:start] + end_marker + text[end + len(end_marker):]
text = text.replace(
    '''        role_collapse_reason="",\n        independent_checked_by=None,\n        independent_checked_at=None,\n        independent_check_role="",\n        independent_check_note="",\n''',
    '''        role_collapse_reason="",\n        admin_override_confirmed=False,\n''',
)
text = text.replace(
    '''        review.role_collapse_reason = ""\n        review.independent_checked_by = None\n        review.independent_checked_at = None\n        review.independent_check_role = ""\n        review.independent_check_note = ""\n''',
    '''        review.role_collapse_reason = ""\n        review.admin_override_confirmed = False\n''',
)
path.write_text(text, encoding="utf-8")

# readiness.py: no generic role-collapse exception remains; an admin override is complete and non-blocking.
path = Path("ki_radar/delivery/readiness.py")
text = path.read_text(encoding="utf-8")
old = '''        elif review.review_status == DeliverySectionReview.ReviewStatus.NEEDS_REVIEW:\n            if (\n                review.has_role_collapse\n                and review.role_confirmations_complete\n                and not review.independent_control_complete\n            ):\n                findings.append(\n                    ReadinessFinding(\n                        section_key,\n                        "INDEPENDENT_CONFIRMATION_MISSING",\n                        "blocker",\n                        (\n                            f"Für „{section_label}“ fehlt nach der zusammengeführten "\n                            "Rollenbestätigung eine unabhängige Kontrolle."\n                        ),\n                    )\n                )\n            else:\n                findings.append(\n                    ReadinessFinding(\n                        section_key,\n                        "SECTION_NEEDS_REVIEW",\n                        "blocker",\n                        f"Die Sektion „{section_label}“ wurde noch nicht vollständig bestätigt.",\n                    )\n                )\n'''
new = '''        elif review.review_status == DeliverySectionReview.ReviewStatus.NEEDS_REVIEW:\n            findings.append(\n                ReadinessFinding(\n                    section_key,\n                    "SECTION_NEEDS_REVIEW",\n                    "blocker",\n                    f"Die Sektion „{section_label}“ wurde noch nicht vollständig bestätigt.",\n                )\n            )\n'''
if old not in text:
    raise RuntimeError("Readiness NEEDS_REVIEW block not found")
text = text.replace(old, new, 1)
old = '''        elif not review.confirmations_complete:\n            code = (\n                "INDEPENDENT_CONFIRMATION_MISSING"\n                if review.has_role_collapse and not review.independent_control_complete\n                else "REQUIRED_CONFIRMATION_MISSING"\n            )\n            message = (\n                f"Für „{section_label}“ fehlt eine unabhängige Kontrolle."\n                if code == "INDEPENDENT_CONFIRMATION_MISSING"\n                else (\n                    f"Für „{section_label}“ fehlen erforderliche fachliche oder "\n                    "technische Bestätigungen."\n                )\n            )\n            findings.append(ReadinessFinding(section_key, code, "blocker", message))\n'''
new = '''        elif not review.confirmations_complete:\n            findings.append(\n                ReadinessFinding(\n                    section_key,\n                    "REQUIRED_CONFIRMATION_MISSING",\n                    "blocker",\n                    (\n                        f"Für „{section_label}“ fehlen erforderliche fachliche oder "\n                        "technische Bestätigungen."\n                    ),\n                )\n            )\n'''
if old not in text:
    raise RuntimeError("Readiness confirmation block not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")

# actions.py: remove obsolete independent-control code.
replace(
    "ki_radar/delivery/actions.py",
    '    "INDEPENDENT_CONFIRMATION_MISSING",\n',
    "",
)

# views.py: expose override controls only to technical admins and remove independent-check UI state.
replace(
    "ki_radar/delivery/views.py",
    '''    can_edit_package,\n    can_independently_check,\n    can_review_section,\n''',
    '''    can_edit_package,\n    can_review_section,\n    can_use_admin_confirmation_override,\n''',
)
replace(
    "ki_radar/delivery/views.py",
    '        "section_reviews__independent_checked_by",\n',
    "",
)
replace(
    "ki_radar/delivery/views.py",
    '''                "can_independent_check": bool(\n                    review and can_independently_check(request.user, package, review)\n                ),\n                "show_role_collapse_reason": bool(\n                    shared_section\n                    and package.use_case.business_owner_id == request.user.id\n                    and package.use_case.technical_owner_id == request.user.id\n                ),\n''',
    '''                "show_admin_override_reason": bool(\n                    shared_section and can_use_admin_confirmation_override(request.user)\n                ),\n''',
)

# Template: exact audit wording requested by the user; no generic exception path.
path = Path("templates/delivery/package_detail.html")
text = path.read_text(encoding="utf-8")
old = '''        {% if row.review.has_role_collapse %}\n        <div class="alert alert-warning py-2 small mb-2">\n          <strong>Keine unabhängige Vier-Augen-Bestätigung.</strong> {{ row.review.role_collapse_reason }}\n          {% if row.review.independent_checked_by %}<br>Unabhängig kontrolliert durch {{ row.review.independent_checked_by }} · {{ row.review.independent_check_role }} · {{ row.review.independent_checked_at|date:"d.m.Y H:i" }}{% else %}<br>Vor „Bereit zur Übergabe“ ist eine Kontrolle durch eine andere fachlich oder technisch berechtigte Person erforderlich.{% endif %}\n        </div>\n        {% endif %}\n'''
new = '''        {% if row.review.admin_override_confirmed %}\n        <div class="alert alert-warning py-2 small mb-2">\n          <strong>Admin-Sonderbestätigung ohne Vier-Augen-Prinzip.</strong> {{ row.review.role_collapse_reason }}\n        </div>\n        {% endif %}\n'''
if old not in text:
    raise RuntimeError("Template audit block not found")
text = text.replace(old, new, 1)
old = '''          {% if row.show_role_collapse_reason and row.can_confirm_business or row.show_role_collapse_reason and row.can_confirm_technical %}\n          <label class="form-label small" for="role-collapse-{{ row.key }}">Begründung bei Bestätigung beider Rollen durch dieselbe Person</label>\n          <input class="form-control form-control-sm mb-2" id="role-collapse-{{ row.key }}" name="role_collapse_reason" value="{% if row.review %}{{ row.review.role_collapse_reason }}{% endif %}">\n          <div class="small text-muted mb-2">Nur erforderlich, sobald du in dieser Sektion auch die zweite Rolle selbst bestätigst.</div>\n          {% endif %}\n'''
new = '''          {% if row.show_admin_override_reason and row.can_confirm_business or row.show_admin_override_reason and row.can_confirm_technical %}\n          <label class="form-label small" for="role-collapse-{{ row.key }}">Begründung der Admin-Sonderbestätigung</label>\n          <input class="form-control form-control-sm mb-2" id="role-collapse-{{ row.key }}" name="role_collapse_reason" value="{% if row.review %}{{ row.review.role_collapse_reason }}{% endif %}">\n          <div class="small text-muted mb-2">Nur verwenden, wenn du als Technischer Administrator zu Admin- oder Testzwecken beide Rollen selbst bestätigst.</div>\n          {% endif %}\n'''
if old not in text:
    raise RuntimeError("Template override input block not found")
text = text.replace(old, new, 1)
text = text.replace(
    '            {% if row.can_independent_check %}<button class="btn btn-sm btn-primary" name="action" value="independent_check">Unabhängig kontrollieren</button>{% endif %}\n',
    "",
)
path.write_text(text, encoding="utf-8")

# Tests: remove obsolete generic collapse path and cover the admin-only exception and exact labels.
path = Path("tests/test_delivery_readiness_v2.py")
text = path.read_text(encoding="utf-8")
start = text.index("@pytest.mark.django_db\ndef test_unassigned_person_cannot_silently_confirm_both_roles")
new_tests = '''@pytest.mark.django_db\ndef test_non_admin_cannot_confirm_both_roles(\n    owner, other_owner, coordinator, business_unit\n):\n    use_case = make_approved_use_case(\n        owner=owner,\n        technical_owner=other_owner,\n        coordinator=coordinator,\n        business_unit=business_unit,\n    )\n    package = create_delivery_package(use_case=use_case, actor=coordinator)\n    review_delivery_section(\n        package=package,\n        section_key="solution_direction",\n        action="confirm_business",\n        actor=coordinator,\n    )\n\n    with pytest.raises(ValidationError, match="Technischer Administrator"):\n        review_delivery_section(\n            package=package,\n            section_key="solution_direction",\n            action="confirm_technical",\n            actor=coordinator,\n            role_collapse_reason="Testdurchlauf.",\n        )\n\n\n@pytest.mark.django_db\ndef test_dual_owner_is_not_an_exception(owner, business_unit, coordinator):\n    use_case = make_approved_use_case(\n        owner=owner,\n        technical_owner=owner,\n        coordinator=coordinator,\n        business_unit=business_unit,\n    )\n    package = create_delivery_package(use_case=use_case, actor=coordinator)\n    review_delivery_section(\n        package=package,\n        section_key="solution_direction",\n        action="confirm_business",\n        actor=owner,\n    )\n\n    with pytest.raises(ValidationError, match="Technischer Administrator"):\n        review_delivery_section(\n            package=package,\n            section_key="solution_direction",\n            action="confirm_technical",\n            actor=owner,\n            role_collapse_reason="Kleines Team.",\n        )\n\n\n@pytest.mark.django_db\ndef test_technical_admin_can_use_audited_same_person_exception(\n    owner, other_owner, coordinator, technical_admin, business_unit\n):\n    use_case = make_approved_use_case(\n        owner=owner,\n        technical_owner=other_owner,\n        coordinator=coordinator,\n        business_unit=business_unit,\n    )\n    package = create_delivery_package(use_case=use_case, actor=coordinator)\n    review_delivery_section(\n        package=package,\n        section_key="solution_direction",\n        action="confirm_business",\n        actor=technical_admin,\n    )\n\n    with pytest.raises(ValidationError, match="Admin-Sonderbestätigung"):\n        review_delivery_section(\n            package=package,\n            section_key="solution_direction",\n            action="confirm_technical",\n            actor=technical_admin,\n        )\n\n    review_delivery_section(\n        package=package,\n        section_key="solution_direction",\n        action="confirm_technical",\n        actor=technical_admin,\n        role_collapse_reason="Vollständiger administrativer Test des Delivery-Flows.",\n    )\n    review = package.section_reviews.get(section_key="solution_direction")\n\n    assert review.admin_override_confirmed is True\n    assert review.has_role_collapse is True\n    assert review.review_status == DeliverySectionReview.ReviewStatus.CONFIRMED\n    assert review.business_confirmation_role == "Admin-Sonderbestätigung"\n    assert review.technical_confirmation_role == "Admin-Sonderbestätigung"\n    assert review.role_collapse_reason.startswith("Vollständiger administrativer Test")\n\n\n@pytest.mark.django_db\ndef test_delivery_page_labels_admin_override_by_confirmation_role(\n    client, owner, other_owner, coordinator, technical_admin, business_unit\n):\n    use_case = make_approved_use_case(\n        owner=owner,\n        technical_owner=other_owner,\n        coordinator=coordinator,\n        business_unit=business_unit,\n    )\n    package = create_delivery_package(use_case=use_case, actor=coordinator)\n    review_delivery_section(\n        package=package,\n        section_key="solution_direction",\n        action="confirm_business",\n        actor=technical_admin,\n    )\n    review_delivery_section(\n        package=package,\n        section_key="solution_direction",\n        action="confirm_technical",\n        actor=technical_admin,\n        role_collapse_reason="Administrativer Ende-zu-Ende-Test.",\n    )\n    client.force_login(technical_admin)\n\n    response = client.get(package.get_absolute_url())\n    body = response.content.decode()\n\n    assert response.status_code == 200\n    assert f"Fachlich: {technical_admin} · Admin-Sonderbestätigung" in body\n    assert f"Technisch: {technical_admin} · Admin-Sonderbestätigung" in body\n    assert "Admin-Sonderbestätigung ohne Vier-Augen-Prinzip" in body\n    assert "Administrativer Ende-zu-Ende-Test" in body\n'''
text = text[:start] + new_tests + "\n"
path.write_text(text, encoding="utf-8")

# Fix the Ruff finding from the interrupted CI run.
replace(
    "tests/test_guided_workflow_ux.py",
    "from ki_radar.delivery.actions import build_actionable_findings, primary_delivery_action\n",
    "from ki_radar.delivery.actions import primary_delivery_action\n",
)
