import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


LEVEL_CHOICES = [("low", "Niedrig"), ("medium", "Mittel"), ("high", "Hoch")]
CONFIDENCE_CHOICES = [("low", "Niedrig"), ("medium", "Mittel"), ("high", "Hoch")]


class Migration(migrations.Migration):
    dependencies = [
        ("use_cases", "0002_decision_quality_metrics"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="StrategicObjective",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("active_from", models.DateField(blank=True, null=True)),
                ("active_until", models.DateField(blank=True, null=True)),
                ("target_kpi", models.CharField(blank=True, max_length=200)),
                ("target_value", models.CharField(blank=True, max_length=200)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="owned_strategic_objectives",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-is_active", "title"],
                "indexes": [
                    models.Index(
                        fields=["is_active", "active_until"],
                        name="use_cases_obj_active_until_idx",
                    )
                ],
            },
        ),
        migrations.AddField(
            model_name="usecase",
            name="strategic_objective",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="use_cases",
                to="use_cases.strategicobjective",
            ),
        ),
        migrations.AddField(
            model_name="usecase",
            name="strategy_contribution",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="historicalusecase",
            name="strategic_objective",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="use_cases.strategicobjective",
            ),
        ),
        migrations.AddField(
            model_name="historicalusecase",
            name="strategy_contribution",
            field=models.TextField(blank=True),
        ),
        migrations.AddIndex(
            model_name="usecase",
            index=models.Index(
                fields=["strategic_objective", "status"],
                name="usecase_strategy_status_idx",
            ),
        ),
        migrations.CreateModel(
            name="DecisionAssessment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("version", models.PositiveIntegerField()),
                ("assessment_date", models.DateField()),
                ("business_value", models.CharField(choices=LEVEL_CHOICES, max_length=10)),
                (
                    "business_value_confidence",
                    models.CharField(choices=CONFIDENCE_CHOICES, max_length=10),
                ),
                ("business_value_rationale", models.TextField()),
                ("business_value_evidence_url", models.URLField(blank=True)),
                ("strategic_fit", models.CharField(choices=LEVEL_CHOICES, max_length=10)),
                (
                    "strategic_fit_confidence",
                    models.CharField(choices=CONFIDENCE_CHOICES, max_length=10),
                ),
                ("strategic_fit_rationale", models.TextField()),
                ("strategic_fit_evidence_url", models.URLField(blank=True)),
                (
                    "technical_feasibility",
                    models.CharField(choices=LEVEL_CHOICES, max_length=10),
                ),
                (
                    "technical_feasibility_confidence",
                    models.CharField(choices=CONFIDENCE_CHOICES, max_length=10),
                ),
                ("technical_feasibility_rationale", models.TextField()),
                ("technical_feasibility_evidence_url", models.URLField(blank=True)),
                ("data_readiness", models.CharField(choices=LEVEL_CHOICES, max_length=10)),
                (
                    "data_readiness_confidence",
                    models.CharField(choices=CONFIDENCE_CHOICES, max_length=10),
                ),
                ("data_readiness_rationale", models.TextField()),
                ("data_readiness_evidence_url", models.URLField(blank=True)),
                (
                    "risk_complexity",
                    models.CharField(choices=LEVEL_CHOICES, max_length=10),
                ),
                (
                    "risk_complexity_confidence",
                    models.CharField(choices=CONFIDENCE_CHOICES, max_length=10),
                ),
                ("risk_complexity_rationale", models.TextField()),
                ("risk_complexity_evidence_url", models.URLField(blank=True)),
                ("overall_rationale", models.TextField(blank=True)),
                (
                    "assessed_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="decision_assessments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "use_case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="decision_assessments",
                        to="use_cases.usecase",
                    ),
                ),
            ],
            options={
                "ordering": ["-version"],
                "indexes": [
                    models.Index(
                        fields=["use_case", "-assessment_date"],
                        name="use_cases_assessment_date_idx",
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("use_case", "version"),
                        name="unique_assessment_version_per_use_case",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="BenefitMeasurement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("measured_at", models.DateField(db_index=True)),
                ("period", models.CharField(max_length=200)),
                ("actual_value", models.DecimalField(decimal_places=4, max_digits=14)),
                ("method", models.TextField()),
                ("evidence_url", models.URLField()),
                ("variance_reason", models.TextField(blank=True)),
                ("decision_consequence", models.TextField(blank=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="benefit_measurements",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "use_case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="benefit_measurements",
                        to="use_cases.usecase",
                    ),
                ),
            ],
            options={
                "ordering": ["-measured_at", "-created_at"],
                "indexes": [
                    models.Index(
                        fields=["use_case", "-measured_at"],
                        name="use_cases_benefit_date_idx",
                    )
                ],
            },
        ),
    ]
