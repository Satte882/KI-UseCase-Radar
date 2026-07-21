# KI-Radar

[![KI-Radar CI](https://github.com/Satte882/KI-UseCase-Radar/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Satte882/KI-UseCase-Radar/actions/workflows/ci.yml)

KI-Radar ist eine branchenneutrale Django-Anwendung zur evidenzbasierten Steuerung von KI-Ideen, Prüfungen, Piloten und produktiven KI-Anwendungen in KMU.

## Produktkern

KI-Radar ist kein Ideenkatalog und kein Projektmanagementsystem. Es verbindet:

`Strategisches Ziel → Bewertungsevidenz → Investitionsentscheidung → reales Ergebnis → Lernen`

Damit stellt die Anwendung sicher, dass:

- kein Pilot ohne messbare Nutzenhypothese startet,
- KI-Vorhaben einem konkreten strategischen Ziel und Wirkbeitrag zugeordnet werden können,
- qualitative Bewertungen versioniert mit Begründung, Nachweis und Evidenzsicherheit dokumentiert werden,
- Pilotziele über eine strukturierte primäre Erfolgsmetrik bewertet werden,
- Nutzenmessungen nach Pilot und Go-live als Historie erhalten bleiben,
- Zielabweichungen mit Ursache und Entscheidungskonsequenz dokumentiert werden,
- ein Go-live nicht ohne Ist-Wert, Messnachweis, Verantwortlichkeiten und erforderliche Fachprüfungen erfolgt,
- anstehende Entscheidungen nach Überfälligkeit und Blockern priorisiert werden,
- alle Beschlüsse, Ausnahmen und offenen Maßnahmen nachvollziehbar bleiben.

## Kernfunktionen

- fünfstufiger Lifecycle: Idee, Prüfung, Pilot, Betrieb, Beendet
- Verwaltung strategischer Ziele mit Verantwortlichkeit, Gültigkeit und Ziel-KPI
- Verknüpfung von Use Cases mit strategischem Ziel und konkretem Wirkbeitrag
- versionierte Kriterienbewertung für Business Value, strategischen Fit, technische Machbarkeit, Datenreife sowie Risiko und Komplexität
- Evidenzsicherheit und kriterienspezifische Begründungs- und Nachweisfelder
- Decision-Readiness-Checks für Pilotstart und Go-live
- strukturierte Baseline-, Ziel- und Ist-Messung mit Einheit, Messmethode und Nachweis
- fortlaufende Nutzenmessungen mit Abweichungsursache und Entscheidungskonsequenz
- Portfolio-Dashboard mit Strategie-, Bewertungs- und Nutzenabdeckung
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

Nach dem Update sind die neuen Tabellen mit folgendem Befehl anzulegen:

```bash
python manage.py migrate
```

## Dokumentation

- [SPECIFICATION.md](SPECIFICATION.md)
- [SETUP.md](SETUP.md)
- [OPERATIONS.md](docs/OPERATIONS.md)
- [BACKUP_RESTORE.md](docs/BACKUP_RESTORE.md)
- [MONITORING.md](docs/MONITORING.md)
- [SECURITY.md](docs/SECURITY.md)
- [Architecture Decision Records](docs/adr/)
