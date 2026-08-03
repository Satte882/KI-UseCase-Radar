from pathlib import Path


def replace(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected block not found in {path}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace(
    "ki_radar/delivery/permissions.py",
    '''            package.use_case.business_owner_id == user.id
            or in_group(user, GROUP_BUSINESS_OWNER)
            or in_group(user, GROUP_COORDINATOR)
''',
    '''            package.use_case.business_owner_id == user.id
            or in_group(user, GROUP_BUSINESS_OWNER)
            or in_group(user, GROUP_COORDINATOR)
            or is_technical_admin(user)
''',
)

old_helper = '''    for review in package.section_reviews.all():
        review_delivery_section(
            package=package,
            section_key=review.section_key,
            action="confirm",
            actor=package.created_by,
            note="Inhalt für Delivery geprüft.",
        )
'''
new_helper = '''    business_actor = package.use_case.business_owner
    technical_actor = package.use_case.technical_owner
    if technical_actor is None or technical_actor.pk == business_actor.pk:
        technical_actor = package.created_by

    for review in package.section_reviews.all():
        if "business" in review.required_confirmations:
            review_delivery_section(
                package=package,
                section_key=review.section_key,
                action="confirm_business",
                actor=business_actor,
                note="Fachlicher Inhalt für Delivery geprüft.",
            )
        if "technical" in review.required_confirmations:
            review_delivery_section(
                package=package,
                section_key=review.section_key,
                action="confirm_technical",
                actor=technical_actor,
                note="Technischer Inhalt für Delivery geprüft.",
            )
'''
replace("tests/test_delivery_handover.py", old_helper, new_helper)
replace("tests/test_delivery_to_pilot.py", old_helper, new_helper)

replace(
    "tests/test_guided_workflow_ux.py",
    '    assert "bei „Nicht relevant“ verpflichtend" in body\n',
    '    assert "bei Blockierung oder „Nicht relevant“ verpflichtend" in body\n',
)
