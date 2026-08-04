from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from ki_radar.architecture.models import ValueStream

ISSUE_NUMBER = 106
TARGET_NAME = "[Real-DEMO] Beschaffungsbedarf bis Bestellung"
REAL_DEMO_PREFIX = "[Real-DEMO]"


class Command(BaseCommand):
    help = (
        "Inspect and correct the Issue #106 Real-DEMO scope record using an explicit, "
        "optimistically locked correction plan."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--inspect",
            action="store_true",
            help="Read the exact target and all Real-DEMO value streams without changing data.",
        )
        parser.add_argument(
            "--plan",
            type=Path,
            help="Absolute path to a private JSON correction plan outside the repository.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply a validated plan. Without this flag, plan execution is a dry run.",
        )
        parser.add_argument(
            "--audit-path",
            type=Path,
            help="Absolute path for the private Markdown audit record outside the repository.",
        )

    def handle(self, *args, **options):
        inspect = options["inspect"]
        plan_path = options["plan"]
        apply = options["apply"]
        audit_path = options["audit_path"]

        if inspect:
            if plan_path or apply or audit_path:
                raise CommandError("--inspect cannot be combined with --plan, --apply or --audit-path.")
            self._inspect()
            return

        if plan_path is None:
            raise CommandError("Use --inspect or provide --plan.")
        if audit_path is not None and not apply:
            raise CommandError("--audit-path is only valid together with --apply.")
        if apply and audit_path is None:
            raise CommandError("--apply requires --audit-path.")

        private_plan_path = self._private_path(plan_path, "Plan")
        plan = self._load_plan(private_plan_path)
        validated = self._validate_plan(plan)
        private_audit_path = (
            self._private_path(audit_path, "Audit") if audit_path is not None else None
        )
        self._execute(validated, apply=apply, audit_path=private_audit_path)

    def _inspect(self) -> None:
        target_rows = list(ValueStream.objects.filter(name=TARGET_NAME).order_by("id"))
        if not target_rows:
            raise CommandError(f'No value stream named "{TARGET_NAME}" exists in this database.')
        if len(target_rows) > 1:
            ids = ", ".join(str(item.pk) for item in target_rows)
            raise CommandError(f'Target name is not unique. Matching IDs: {ids}')

        payload = {
            "issue": ISSUE_NUMBER,
            "mode": "inspection",
            "target": self._serialize_stream(target_rows[0]),
            "real_demo_value_streams": self._real_demo_snapshot(),
            "next_step": (
                "Review every listed Real-DEMO stream, then create a private correction plan "
                "with exact values. No value is inferred or split automatically."
            ),
        }
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

    def _execute(
        self,
        plan: dict[str, Any],
        *,
        apply: bool,
        audit_path: Path | None,
    ) -> None:
        target_plan = plan["target"]
        expected_updated_at = target_plan["expected_updated_at_parsed"]
        prepared_audit: dict[str, Any] | None = None

        with transaction.atomic():
            real_demo_rows = list(
                ValueStream.objects.select_for_update()
                .filter(name__startswith=REAL_DEMO_PREFIX)
                .order_by("name", "id")
            )
            inventory_ids = {str(item.pk) for item in real_demo_rows}
            reviewed_ids = set(plan["real_demo_review"]["reviewed_ids"])
            if inventory_ids != reviewed_ids:
                missing_review = sorted(inventory_ids - reviewed_ids)
                absent_now = sorted(reviewed_ids - inventory_ids)
                raise CommandError(
                    "Real-DEMO inventory changed or was not fully reviewed. "
                    f"Unreviewed current IDs: {missing_review}; IDs no longer present: {absent_now}."
                )

            try:
                target = next(
                    item
                    for item in real_demo_rows
                    if str(item.pk) == target_plan["id"] and item.name == TARGET_NAME
                )
            except StopIteration as exc:
                raise CommandError(
                    "The exact target UUID and name from the plan do not match a current record."
                ) from exc

            mismatches = []
            if target.scope_in != target_plan["expected_scope_in"]:
                mismatches.append("scope_in")
            if target.scope_out != target_plan["expected_scope_out"]:
                mismatches.append("scope_out")
            if target.updated_at != expected_updated_at:
                mismatches.append("updated_at")
            if mismatches:
                raise CommandError(
                    "Optimistic lock failed. Current data differs from the inspected plan in: "
                    + ", ".join(mismatches)
                    + ". Run --inspect again and review the record before changing anything."
                )

            before = self._serialize_stream(target)
            after_planned = {
                **before,
                "scope_in": target_plan["new_scope_in"],
                "scope_out": target_plan["new_scope_out"],
            }
            summary = self._public_summary(
                plan=plan,
                before=before,
                after=after_planned,
                status="validated_no_change" if not apply else "prepared",
            )

            if not apply:
                self.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
                return

            if audit_path is None:
                raise CommandError("Internal error: audit path missing for apply mode.")
            if audit_path.exists():
                raise CommandError(f"Audit path already exists and will not be overwritten: {audit_path}")

            prepared_audit = self._audit_payload(
                plan=plan,
                status="PREPARED",
                before=before,
                after=after_planned,
                inventory=[self._serialize_stream(item) for item in real_demo_rows],
                changed_rows=0,
            )
            self._write_new_audit(audit_path, prepared_audit)

            changed_at = timezone.now()
            changed_rows = ValueStream.objects.filter(
                pk=target.pk,
                name=TARGET_NAME,
                scope_in=target_plan["expected_scope_in"],
                scope_out=target_plan["expected_scope_out"],
                updated_at=expected_updated_at,
            ).update(
                scope_in=target_plan["new_scope_in"],
                scope_out=target_plan["new_scope_out"],
                updated_at=changed_at,
            )
            if changed_rows != 1:
                raise CommandError(
                    f"Expected exactly one changed row, but the database reported {changed_rows}."
                )

            target.refresh_from_db()
            if (
                target.scope_in != target_plan["new_scope_in"]
                or target.scope_out != target_plan["new_scope_out"]
            ):
                raise CommandError("Post-update verification failed; transaction was rolled back.")

            after = self._serialize_stream(target)
            inventory_after = self._real_demo_snapshot()
            prepared_audit = self._audit_payload(
                plan=plan,
                status="APPLIED",
                before=before,
                after=after,
                inventory=inventory_after,
                changed_rows=changed_rows,
            )

        if audit_path is None or prepared_audit is None:
            raise CommandError("Internal error: applied correction has no audit payload.")
        self._replace_audit(audit_path, prepared_audit)
        audit_hash = hashlib.sha256(audit_path.read_bytes()).hexdigest()
        result = self._public_summary(
            plan=plan,
            before=prepared_audit["target"]["before"],
            after=prepared_audit["target"]["after"],
            status="applied",
        )
        result.update(
            {
                "changed_rows": 1,
                "audit_path": str(audit_path),
                "audit_sha256": audit_hash,
            }
        )
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))

    def _load_plan(self, path: Path) -> dict[str, Any]:
        if not path.is_file():
            raise CommandError(f"Plan file does not exist: {path}")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Cannot read valid JSON plan {path}: {exc}") from exc
        if not isinstance(value, dict):
            raise CommandError("The correction plan must be a JSON object.")
        return value

    def _validate_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        if plan.get("issue") != ISSUE_NUMBER:
            raise CommandError(f"Plan field 'issue' must be {ISSUE_NUMBER}.")

        for field in (
            "environment",
            "operator",
            "backup_reference",
            "repository_check_reference",
        ):
            self._required_text(plan, field)

        target = plan.get("target")
        if not isinstance(target, dict):
            raise CommandError("Plan field 'target' must be an object.")
        if target.get("name") != TARGET_NAME:
            raise CommandError(f"Plan target name must be exactly: {TARGET_NAME}")
        try:
            target_id = str(UUID(self._required_text(target, "id")))
        except ValueError as exc:
            raise CommandError("Plan target 'id' must be a valid UUID.") from exc

        expected_updated_at_text = self._required_text(target, "expected_updated_at")
        expected_updated_at = parse_datetime(expected_updated_at_text)
        if expected_updated_at is None:
            raise CommandError("Plan target 'expected_updated_at' must be an ISO-8601 datetime.")
        if timezone.is_naive(expected_updated_at):
            expected_updated_at = timezone.make_aware(expected_updated_at)

        for field in (
            "expected_scope_in",
            "expected_scope_out",
            "new_scope_in",
            "new_scope_out",
        ):
            if field not in target or not isinstance(target[field], str):
                raise CommandError(f"Plan target '{field}' must be a string.")
        if not target["new_scope_in"].strip():
            raise CommandError("Plan target 'new_scope_in' must not be empty.")
        if not target["new_scope_out"].strip():
            raise CommandError("Plan target 'new_scope_out' must not be empty.")
        if (
            target["expected_scope_in"] == target["new_scope_in"]
            and target["expected_scope_out"] == target["new_scope_out"]
        ):
            raise CommandError("The plan does not change scope_in or scope_out.")

        review = plan.get("real_demo_review")
        if not isinstance(review, dict):
            raise CommandError("Plan field 'real_demo_review' must be an object.")
        reviewed_ids = review.get("reviewed_ids")
        if not isinstance(reviewed_ids, list) or not reviewed_ids:
            raise CommandError("real_demo_review.reviewed_ids must be a non-empty list.")
        normalized_ids = []
        for value in reviewed_ids:
            try:
                normalized_ids.append(str(UUID(str(value))))
            except ValueError as exc:
                raise CommandError(
                    "Every real_demo_review.reviewed_ids value must be a valid UUID."
                ) from exc
        if len(normalized_ids) != len(set(normalized_ids)):
            raise CommandError("real_demo_review.reviewed_ids contains duplicates.")
        if target_id not in normalized_ids:
            raise CommandError("The target UUID must be included in reviewed_ids.")
        self._required_text(review, "conclusion")

        validated = dict(plan)
        validated["target"] = {
            **target,
            "id": target_id,
            "expected_updated_at_parsed": expected_updated_at,
        }
        validated["real_demo_review"] = {**review, "reviewed_ids": normalized_ids}
        return validated

    def _private_path(self, path: Path | None, label: str) -> Path:
        if path is None:
            raise CommandError(f"{label} path is missing.")
        if not path.is_absolute():
            raise CommandError(f"{label} path must be absolute.")
        resolved = path.resolve()
        try:
            resolved.relative_to(Path.cwd().resolve())
        except ValueError:
            return resolved
        raise CommandError(
            f"{label} path must be outside the repository/current working directory: {resolved}"
        )

    def _real_demo_snapshot(self) -> list[dict[str, Any]]:
        return [
            self._serialize_stream(item)
            for item in ValueStream.objects.filter(name__startswith=REAL_DEMO_PREFIX).order_by(
                "name", "id"
            )
        ]

    @staticmethod
    def _serialize_stream(stream: ValueStream) -> dict[str, Any]:
        return {
            "id": str(stream.pk),
            "name": stream.name,
            "scope_in": stream.scope_in,
            "scope_out": stream.scope_out,
            "updated_at": stream.updated_at.isoformat(),
        }

    @staticmethod
    def _required_text(mapping: dict[str, Any], field: str) -> str:
        value = mapping.get(field)
        if not isinstance(value, str) or not value.strip():
            raise CommandError(f"Plan field '{field}' must be a non-empty string.")
        return value

    def _public_summary(
        self,
        *,
        plan: dict[str, Any],
        before: dict[str, Any],
        after: dict[str, Any],
        status: str,
    ) -> dict[str, Any]:
        return {
            "issue": ISSUE_NUMBER,
            "status": status,
            "environment": plan["environment"],
            "target_id": plan["target"]["id"],
            "target_name": TARGET_NAME,
            "before": {
                "scope_in_sha256": self._text_hash(before["scope_in"]),
                "scope_out_sha256": self._text_hash(before["scope_out"]),
                "updated_at": before["updated_at"],
            },
            "after": {
                "scope_in_sha256": self._text_hash(after["scope_in"]),
                "scope_out_sha256": self._text_hash(after["scope_out"]),
                "updated_at": after["updated_at"],
            },
            "reviewed_real_demo_ids": plan["real_demo_review"]["reviewed_ids"],
            "review_conclusion": plan["real_demo_review"]["conclusion"],
        }

    @staticmethod
    def _audit_payload(
        *,
        plan: dict[str, Any],
        status: str,
        before: dict[str, Any],
        after: dict[str, Any],
        inventory: list[dict[str, Any]],
        changed_rows: int,
    ) -> dict[str, Any]:
        return {
            "issue": ISSUE_NUMBER,
            "status": status,
            "environment": plan["environment"],
            "operator": plan["operator"],
            "backup_reference": plan["backup_reference"],
            "repository_check_reference": plan["repository_check_reference"],
            "recorded_at": timezone.now().isoformat(),
            "target": {"before": before, "after": after},
            "changed_rows": changed_rows,
            "real_demo_review": {
                **plan["real_demo_review"],
                "inventory_after_operation": inventory,
            },
        }

    def _write_new_audit(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        content = self._audit_markdown(payload)
        try:
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
        except OSError as exc:
            raise CommandError(f"Cannot create private audit file {path}: {exc}") from exc

    def _replace_audit(self, path: Path, payload: dict[str, Any]) -> None:
        content = self._audit_markdown(payload)
        try:
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                newline="\n",
                dir=path.parent,
                delete=False,
            ) as handle:
                handle.write(content)
                temporary_path = Path(handle.name)
            os.replace(temporary_path, path)
        except OSError as exc:
            raise CommandError(
                f"Database correction committed, but final audit replacement failed: {exc}. "
                f"The PREPARED audit remains at {path}; investigate before retrying."
            ) from exc

    @staticmethod
    def _audit_markdown(payload: dict[str, Any]) -> str:
        serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        return (
            "# Datenkorrektur Issue #106\n\n"
            "Diese Datei enthält fachliche Daten und muss privat aufbewahrt werden. "
            "Sie darf nicht in das öffentliche Repository committed werden.\n\n"
            f"```json\n{serialized}\n```\n"
        )

    @staticmethod
    def _text_hash(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
