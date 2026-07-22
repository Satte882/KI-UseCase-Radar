import os
import secrets

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ki_radar.core.demo_architecture_data import (
    DOCUMENT_USE_CASE_KEY,
    INVOICE_USE_CASE_KEY,
    seed_demo_architecture_data,
)
from ki_radar.core.demo_data import seed_demo_data
from ki_radar.core.demo_decision_data import enrich_demo_metrics
from ki_radar.core.demo_identity import assign_demo_identities, prepare_demo_identities
from ki_radar.use_cases.models import UseCase


class Command(BaseCommand):
    help = "Create or restore the reproducible KI-Radar demo dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            dest="demo_user_password",
            help="Password for all demo users. Defaults to DEMO_USER_PASSWORD or a random value.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "seed_demo_data is only allowed with DEBUG=True. "
                "Do not create demo users in staging or production."
            )

        password = options["demo_user_password"] or os.getenv("DEMO_USER_PASSWORD")
        generated_password = password is None
        if generated_password:
            password = secrets.token_urlsafe(18)
        elif not password.strip():
            raise CommandError("Demo user password must not be empty.")

        prepare_demo_identities()
        counts = seed_demo_data(demo_user_password=password)
        metric_count = enrich_demo_metrics()
        architecture_counts = seed_demo_architecture_data()
        assign_demo_identities()
        UseCase.objects.filter(
            demo_key__in=[INVOICE_USE_CASE_KEY, DOCUMENT_USE_CASE_KEY]
        ).update(status=UseCase.Status.REVIEW)
        self.stdout.write(
            self.style.SUCCESS(
                "Demo-Daten eingespielt: "
                f"{counts['business_units']} Organisationseinheiten, "
                f"{counts['users']} Benutzer, "
                f"{counts['use_cases']} Use Cases, "
                f"{counts['governance_assessments']} Governance-Screenings, "
                f"{counts['reviews']} Reviews, "
                f"{metric_count} strukturierte Erfolgsmetriken, "
                f"{architecture_counts['value_streams']} Value Streams, "
                f"{architecture_counts['process_analyses']} Prozessanalysen, "
                f"{architecture_counts['solution_options']} Lösungsoptionen und "
                f"{architecture_counts['delivery_packages']} Delivery Packages."
            )
        )
        if generated_password:
            self.stdout.write(
                self.style.WARNING("Zufaelliges Demo-Passwort fuer alle Demo-Benutzer: " + password)
            )
        else:
            self.stdout.write("Demo-Benutzerpasswort aus Option oder DEMO_USER_PASSWORD gesetzt.")
