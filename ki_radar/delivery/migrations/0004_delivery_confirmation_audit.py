import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("delivery", "0003_delivery_readiness_v2"),
    ]

    operations = [
        migrations.AddField(
            model_name="deliverysectionreview",
            name="business_confirmation_role",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="deliverysectionreview",
            name="technical_confirmation_role",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="deliverysectionreview",
            name="role_collapse_reason",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="deliverysectionreview",
            name="independent_checked_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="independently_checked_delivery_sections",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="deliverysectionreview",
            name="independent_checked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="deliverysectionreview",
            name="independent_check_role",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="deliverysectionreview",
            name="independent_check_note",
            field=models.TextField(blank=True),
        ),
    ]
