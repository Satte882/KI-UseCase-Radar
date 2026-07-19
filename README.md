# KI-Radar

KI-Radar ist eine branchenneutrale Django-Anwendung zur transparenten Steuerung von KI-Ideen, Prüfungen, Piloten und produktiven KI-Anwendungen in KMU.

## Kernfunktionen

- fünfstufiger Lifecycle: Idee, Prüfung, Pilot, Betrieb, Beendet
- rollenbasierter Zugriff für technischen Administrator, KI-Koordinator, Business Owner und Leser
- Governance-Screening ohne automatische Rechtsklassifizierung
- Review- und Entscheidungshistorie
- technische Änderungshistorie mit `django-simple-history`
- Dashboard, Monatsreview, Suche, Filter und CSV-Export
- datenschutzgerechter Anonymisierungsprozess mit externem Wiederanwendungs-Ledger
- Health-Endpunkte, Sentry-Integration und operative Job-Überwachung
- getrennte Docker-Stacks für lokale Entwicklung, Staging und Produktion
- Backup- und Restore-Skripte sowie CI-Pipeline

## Schnellstart

Siehe [SETUP.md](SETUP.md). Offene externe Betriebsentscheidungen stehen in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

## Dokumentation

- [SPECIFICATION.md](SPECIFICATION.md)
- [SETUP.md](SETUP.md)
- [OPERATIONS.md](docs/OPERATIONS.md)
- [BACKUP_RESTORE.md](docs/BACKUP_RESTORE.md)
- [MONITORING.md](docs/MONITORING.md)
- [SECURITY.md](docs/SECURITY.md)
- [Architecture Decision Records](docs/adr/)
