# KI-Radar

[![KI-Radar CI](https://github.com/Satte882/KI-UseCase-Radar/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Satte882/KI-UseCase-Radar/actions/workflows/ci.yml)

KI-Radar ist eine branchenneutrale Django-Anwendung zur evidenzbasierten Steuerung von KI-Ideen, Prüfungen, Piloten und produktiven KI-Anwendungen in KMU.

## Produktkern

KI-Radar ist kein Ideenkatalog und kein Projektmanagementsystem. Es stellt sicher, dass:

- kein Pilot ohne messbare Nutzenhypothese startet,
- Pilotziele über eine strukturierte primäre Erfolgsmetrik bewertet werden,
- ein Go-live nicht ohne Ist-Wert, Messnachweis, Verantwortlichkeiten und erforderliche Fachprüfungen erfolgt,
- Zielverfehlungen ausdrücklich begründet werden,
- anstehende Entscheidungen nach Überfälligkeit und Blockern priorisiert werden,
- alle Beschlüsse, Ausnahmen und offenen Maßnahmen nachvollziehbar bleiben.

## Kernfunktionen

- fünfstufiger Lifecycle: Idee, Prüfung, Pilot, Betrieb, Beendet
- Decision-Readiness-Checks für Pilotstart und Go-live
- strukturierte Baseline-, Ziel- und Ist-Messung mit Einheit, Messmethode und Nachweis
- priorisierte Entscheidungswarteschlange statt eines reinen Termin-Dashboards
- geführter Review- und Entscheidungsworkflow
- optionaler semantischer Review-Copilot über OpenRouter
- rollenbasierter Zugriff für technischen Administrator, KI-Koordinator, Business Owner und Leser
- Governance-Screening ohne automatische Rechtsklassifizierung
- technische Änderungshistorie mit `django-simple-history`
- Dark-Mode-SaaS-Oberfläche, Suche, Filter und CSV-Export
- datenschutzgerechter Anonymisierungsprozess mit externem Wiederanwendungs-Ledger
- Health-Endpunkte, Sentry-Integration und operative Job-Überwachung
- getrennte Docker-Stacks für lokale Entwicklung, Staging und Produktion
- Backup- und Restore-Skripte sowie CI-Pipeline

## Schnellstart

Siehe [SETUP.md](SETUP.md). Für den optionalen Copilot wird nur `OPENROUTER_API_KEY` in der lokalen `.env` benötigt. Ohne API-Key funktionieren alle verbindlichen Decision-Checks vollständig.

## Dokumentation

- [SPECIFICATION.md](SPECIFICATION.md)
- [SETUP.md](SETUP.md)
- [OPERATIONS.md](docs/OPERATIONS.md)
- [BACKUP_RESTORE.md](docs/BACKUP_RESTORE.md)
- [MONITORING.md](docs/MONITORING.md)
- [SECURITY.md](docs/SECURITY.md)
- [Architecture Decision Records](docs/adr/)
