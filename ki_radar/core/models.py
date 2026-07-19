from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SystemJobRun(TimeStampedModel):
    class Status(models.TextChoices):
        RUNNING = "running", "Läuft"
        SUCCESS = "success", "Erfolgreich"
        FAILED = "failed", "Fehlgeschlagen"

    job_name = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    exit_code = models.IntegerField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["job_name", "-started_at"])]

    def __str__(self) -> str:
        return f"{self.job_name}: {self.status} ({self.started_at:%Y-%m-%d %H:%M})"
