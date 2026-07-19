import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Reapplies anonymizations from the external append-only ledger after a restore."

    def add_arguments(self, parser):
        parser.add_argument("--ledger", default=str(settings.ANONYMIZATION_LEDGER_PATH))
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        path = Path(options["ledger"])
        if not path.exists():
            self.stdout.write(self.style.WARNING("No anonymization ledger found"))
            return
        User = get_user_model()
        count = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            user = User.objects.filter(pk=record["user_id"]).first()
            if not user or user.is_anonymized:
                continue
            count += 1
            if options["dry_run"]:
                continue
            user.username = record["anonymized_username"]
            user.first_name = ""
            user.last_name = ""
            user.email = f"{record['anonymized_username']}@example.invalid"
            user.external_identity_id = ""
            user.job_function = ""
            user.business_unit = None
            user.is_active = False
            user.is_staff = False
            user.is_superuser = False
            user.is_anonymized = True
            user.anonymized_at = timezone.now()
            user.set_unusable_password()
            user.save()
            user.groups.clear()
            user.user_permissions.clear()
        self.stdout.write(
            self.style.SUCCESS(
                f"{'Would reapply' if options['dry_run'] else 'Reapplied'} {count} anonymizations"
            )
        )
