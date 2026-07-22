from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("delivery", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeliveryArchitectureArtifacts",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("system_landscape", models.TextField(blank=True, verbose_name="Ist-/Ziel-Systemlandschaft")),
                ("data_flows", models.TextField(blank=True, verbose_name="Daten- und Informationsflüsse")),
                ("integration_contracts", models.TextField(blank=True, verbose_name="Integrationsverträge und Verantwortlichkeiten")),
                ("artifacts_url", models.URLField(blank=True, verbose_name="Architekturartefakte und Diagramme")),
                ("delivery_package", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="architecture_artifacts", to="delivery.deliverypackage")),
            ],
        ),
    ]
