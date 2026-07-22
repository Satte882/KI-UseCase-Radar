from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("use_cases", "0004_usecase_demo_key"),
    ]

    operations = [
        migrations.CreateModel(
            name="UseCaseClassification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("business_domain", models.CharField(choices=[("procurement", "Einkauf und Beschaffung"), ("sales", "Vertrieb"), ("marketing", "Marketing"), ("production", "Produktion und Leistungserbringung"), ("logistics", "Logistik und Supply Chain"), ("finance", "Finanzen und Controlling"), ("human_resources", "Personal"), ("customer_service", "Kundenservice"), ("it", "IT und Technologie"), ("legal_compliance", "Recht und Compliance"), ("research_development", "Forschung und Entwicklung"), ("corporate_services", "Unternehmensfunktionen"), ("other", "Sonstige Fachdomäne")], db_index=True, default="other", max_length=40, verbose_name="Fachdomäne")),
                ("capability", models.CharField(blank=True, max_length=200, verbose_name="Business Capability")),
                ("process_area", models.CharField(blank=True, max_length=200, verbose_name="Prozessbereich")),
                ("use_case", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="classification", to="use_cases.usecase")),
            ],
            options={"ordering": ["business_domain", "capability", "use_case__short_id"]},
        ),
    ]
