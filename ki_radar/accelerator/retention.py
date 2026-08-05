from __future__ import annotations

from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from .models import CaptureSession

CAPTURE_PURGE_GRACE_DAYS = 7


def expire_due_capture_sessions(*, now=None, owner=None) -> int:
    """Move overdue drafts to the terminal expired state without exposing answers."""
    checked_now = now or timezone.now()
    sessions = CaptureSession.objects.filter(
        status=CaptureSession.Status.DRAFT,
        expires_at__lte=checked_now,
    )
    if owner is not None:
        sessions = sessions.filter(owner=owner)
    return sessions.update(
        status=CaptureSession.Status.EXPIRED,
        expired_at=checked_now,
        updated_at=checked_now,
    )


def expire_capture_session_if_due(session: CaptureSession, *, now=None) -> CaptureSession:
    checked_now = now or timezone.now()
    if session.status != CaptureSession.Status.DRAFT or session.expires_at > checked_now:
        return session

    updated = CaptureSession.objects.filter(
        pk=session.pk,
        status=CaptureSession.Status.DRAFT,
        expires_at__lte=checked_now,
    ).update(
        status=CaptureSession.Status.EXPIRED,
        expired_at=checked_now,
        updated_at=checked_now,
    )
    if updated:
        session.status = CaptureSession.Status.EXPIRED
        session.expired_at = checked_now
        session.updated_at = checked_now
    else:
        session.refresh_from_db()
    return session


def purge_terminal_capture_sessions(
    *,
    now=None,
    grace_days: int = CAPTURE_PURGE_GRACE_DAYS,
) -> int:
    """Physically remove expired or discarded sessions after the grace period."""
    if grace_days < 0:
        raise ValueError("Die Karenzzeit darf nicht negativ sein.")

    checked_now = now or timezone.now()
    cutoff = checked_now - timedelta(days=grace_days)
    sessions = CaptureSession.objects.filter(
        Q(
            status=CaptureSession.Status.EXPIRED,
            expired_at__isnull=False,
            expired_at__lte=cutoff,
        )
        | Q(
            status=CaptureSession.Status.DISCARDED,
            discarded_at__isnull=False,
            discarded_at__lte=cutoff,
        )
    )
    deleted_count = sessions.count()
    sessions.delete()
    return deleted_count
