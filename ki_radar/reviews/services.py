from django.db import transaction

from ki_radar.use_cases.services import apply_status_transition

from .models import Review


@transaction.atomic
def create_review(*, use_case, actor, data) -> Review:
    previous_status = use_case.status
    review_data = data.copy()

    for field in [
        "ending_reason",
        "data_and_access_handling",
        "replacement_solution",
        "final_assessment",
        "lessons_learned",
    ]:
        value = review_data.pop(field, "")
        if value:
            setattr(use_case, field, value)

    use_case.next_review_date = review_data.get("next_review_date")
    target_status = review_data["new_status"]

    if target_status != previous_status:
        apply_status_transition(use_case=use_case, target_status=target_status, actor=actor)
    else:
        use_case._history_user = actor
        use_case.save()

    review = Review(
        use_case=use_case,
        reviewer=actor,
        previous_status=previous_status,
        **review_data,
    )
    review._history_user = actor
    review.save()
    return review
