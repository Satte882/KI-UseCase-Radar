from pathlib import Path


def replace(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected block not found in {path}: {old[:120]!r}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace(
    "tests/test_demo_data.py",
    "assert User.objects.filter(username__in=demo_usernames()).count() == 3",
    "assert User.objects.filter(username__in=demo_usernames()).count() == 4",
)

replace(
    "tests/test_guided_intake_hard_gates.py",
    "from django.core.exceptions import ValidationError\n",
    "from django.core.exceptions import PermissionDenied, ValidationError\n",
)
replace(
    "tests/test_guided_intake_hard_gates.py",
    '''            condition_owner=owner,\n            condition_due_date=timezone.localdate() + timedelta(days=14),\n        ),\n    )\n\n    decision_ready_use_case.refresh_from_db()\n''',
    '''            condition_owner=owner,\n            condition_due_date=timezone.localdate() + timedelta(days=14),\n            second_approval_assignee=second_approver,\n        ),\n    )\n\n    decision_ready_use_case.refresh_from_db()\n''',
)
replace(
    "tests/test_guided_intake_hard_gates.py",
    '''    with pytest.raises(ValidationError, match="weitere unabhängige"):\n        confirm_conditional_decision(decision=decision, actor=approver)\n''',
    '''    with pytest.raises(PermissionDenied, match="Personentrennung"):\n        confirm_conditional_decision(decision=decision, actor=approver)\n''',
)

replace(
    "tests/test_pr_a_enforcement.py",
    "from django.core.exceptions import ValidationError\n",
    "from django.core.exceptions import PermissionDenied, ValidationError\n",
)
replace(
    "tests/test_pr_a_enforcement.py",
    '''    first_approver = make_coordinator("first-approver", business_unit)\n    coordinator_group, _ = Group.objects.get_or_create(name=GROUP_COORDINATOR)\n''',
    '''    first_approver = make_coordinator("first-approver", business_unit)\n    second_approver = make_coordinator("second-approver", business_unit)\n    coordinator_group, _ = Group.objects.get_or_create(name=GROUP_COORDINATOR)\n''',
)
replace(
    "tests/test_pr_a_enforcement.py",
    '''            condition_owner=owner,\n            condition_due_date=timezone.localdate() + timedelta(days=14),\n        ),\n    )\n\n    with pytest.raises(ValidationError, match="fachlich verantwortliche Person"):\n''',
    '''            condition_owner=owner,\n            condition_due_date=timezone.localdate() + timedelta(days=14),\n            second_approval_assignee=second_approver,\n        ),\n    )\n\n    with pytest.raises(PermissionDenied, match="Personentrennung"):\n''',
)
