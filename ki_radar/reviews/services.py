from django.db import transaction
from ki_radar.use_cases.services import apply_status_transition
from .models import Review


@transaction.atomic
def create_review(*, use_case, actor, data) -> Review:
    previous_status = use_case.status
    data = data.copy()
    for field in ["ending_reason", "data_and_access_handling", "replacement_solution", "final_assessment", "lessons_learned"]:
        value = data.pop(field, "")
        if value:
            setattr(use_case, field, value)
    target_status = data["new_status"]
    if target_status != previous_status:
        apply_status_transition(use_case=use_case, target_status=target_status, actor=actor)
    use_case.next_review_date = data.get("next_review_date")
    use_case.save(update_fields=["next_review_date", "updated_at"])
    return Review.objects.create(
        use_case=use_case,
        reviewer=actor,
        previous_status=previous_status,
        **data,
    )
