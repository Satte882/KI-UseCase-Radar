from django.core.management.base import BaseCommand

from ki_radar.core.demo_architecture_data import clear_demo_architecture_data
from ki_radar.core.demo_data import clear_demo_data
from ki_radar.core.demo_identity import prepare_demo_identities


class Command(BaseCommand):
    help = "Remove only the KI-Radar demo dataset created by seed_demo_data."

    def handle(self, *args, **options):
        prepare_demo_identities()
        architecture_counts = clear_demo_architecture_data()
        counts = clear_demo_data()
        self.stdout.write(
            self.style.SUCCESS(
                "Demo-Daten entfernt: "
                f"{counts['business_units']} Organisationseinheiten, "
                f"{counts['users']} Benutzer, "
                f"{counts['use_cases']} Use Cases, "
                f"{counts['governance_assessments']} Governance-Screenings, "
                f"{counts['reviews']} Reviews, "
                f"{architecture_counts['value_streams']} Architecture-Objekte und "
                f"{architecture_counts['architecture_origins']} Herkunftsverknüpfungen."
            )
        )
