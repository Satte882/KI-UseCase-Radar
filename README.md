# KI-Radar

[![KI-Radar CI](https://github.com/Satte882/KI-UseCase-Radar/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Satte882/KI-UseCase-Radar/actions/workflows/ci.yml)

> AI Business Architecture, Portfolio- und Decision-Governance-Cockpit für kleine und mittlere Unternehmen.

KI-Radar verbindet die fachliche Analyse eines Unternehmensbereichs mit der belastbaren Auswahl, Freigabe und Übergabe von KI-Vorhaben an ein Delivery-Team.

```text
Value Stream
→ Prozessanalyse und Bottleneck
→ organisatorische, klassische und KI-Lösungsoptionen
→ geführter Use-Case-Intake
→ evidenzbasierte Bewertung und Freigabe
→ Portfolio-Steuerung
→ versioniertes Delivery Package
→ Umsetzung in Jira, Azure DevOps, GitHub oder einem anderen Delivery-System
```

Der Discovery-Pfad ist optional. Ein Use Case kann weiterhin direkt über den bestehenden Intake erfasst werden. Dadurch eignet sich KI-Radar sowohl für systematische Architekturarbeit als auch für bereits bekannte Einzelvorhaben.

## Welches Problem löst KI-Radar?

In vielen Organisationen sind Informationen über KI-Ideen, Prozessprobleme, Bewertungen, Governance-Prüfungen und Delivery-Anforderungen über Tabellen, Präsentationen, Tickets und einzelne Dokumente verteilt.

KI-Radar beantwortet in einem durchgängigen Arbeitsmodell:

- Wo entsteht im End-to-End-Value-Stream ein relevantes Problem?
- Wie sieht der heutige Prozess mit Rollen, Systemen, Daten, Regeln und Engpässen aus?
- Ist KI tatsächlich die sinnvollste Option oder reicht eine organisatorische beziehungsweise regelbasierte Lösung?
- Welcher messbare Nutzen wird erwartet?
- Wie belastbar sind Nutzen, Machbarkeit, Datenlage und Risiken belegt?
- Welche Governance- und Fachprüfungen fehlen?
- Wer hat welche Entscheidung auf welcher Evidenzbasis getroffen?
- Welche Vorhaben gehören aktiv ins Portfolio?
- Was muss ein Delivery-Team konkret umsetzen und wie wird der MVP abgenommen?

## Produktbereiche

### Analyse

Der Bereich **Analyse** unterstützt einen optionalen Business-Architecture-Pfad.

#### Value-Stream-Analyse

Ein Value Stream beschreibt die End-to-End-Wertschöpfung mit:

- Auslöser und Ergebnis für den Empfänger
- Scope und strategischem Ziel
- Stakeholdern und Leitplanken
- geordneten Hauptphasen
- Rollen, Systemen und Dokumenten je Phase
- Problemen, Engpässen und Baseline-Kennzahlen

Aus einer Phase kann der vorhandene Use-Case-Intake vorbefüllt werden. Alle bestehenden Plausibilitäts- und Hard-Gate-Prüfungen bleiben dabei aktiv.

#### Prozessanalyse

Nur relevante Value-Stream-Phasen werden detailliert analysiert:

- Prozessstart und Prozessende
- Auslöser und Ergebnis
- Ist-Ablauf
- Rollen und Verantwortlichkeiten
- Anwendungen und Arbeitsmittel
- Datenobjekte und Dokumente
- Geschäftsregeln
- Übergaben und Schnittstellen
- Bottlenecks und Ursachen
- Ausnahmen und Fehlerfälle
- Baseline und Prozesskennzahlen
- Prinzipien für einen Soll-Prozess

KI-Radar ist bewusst kein BPMN-Modellierer. Der Schwerpunkt liegt auf entscheidungsrelevanten Artefakten und der nachvollziehbaren Ableitung von Lösungsoptionen.

#### Lösungsoptionen

Eine Prozessanalyse kann mehrere Alternativen enthalten:

- organisatorische Änderung
- regelbasierte Automatisierung
- Standardsoftware
- individuelle Software
- Analytics oder Machine Learning
- generative KI
- Assistenzsystem
- keine technische Lösung

Maximal eine Option wird ausdrücklich als bevorzugt markiert. Nur diese kann in den bestehenden Use-Case-Intake überführt werden. KI wird dadurch nicht automatisch bevorzugt, sondern muss sich gegenüber einfacheren Alternativen begründen.

### Use Cases und Entscheidungen

Der sechsstufige Intake führt von der Problemstellung bis zur Vorprüfung:

1. Problem verstehen
2. Prozess einordnen
3. Nutzung und betroffene Personen klären
4. Nutzenhypothese messbar machen
5. Daten- und Lösungsrahmen erfassen
6. Angaben vor der Bewertung prüfen

Die versionierte Bewertung betrachtet:

- wirtschaftlichen Nutzen
- strategischen Beitrag
- technische Machbarkeit
- Datenreife
- Risiko und Komplexität
- Qualität, Aktualität und Abdeckung der Evidenz
- unabhängige Prüfung
- offene Annahmen

Aus der Evidenzbasis wird eine nachvollziehbare Confidence-Stufe abgeleitet. Bewertung und Freigabe bleiben getrennte Arbeitsschritte.

Mögliche Entscheidungsstatus:

- In Klärung
- Bereit zur Bewertung
- Zurückgestellt
- Freigegeben
- Freigegeben mit Auflagen
- Nicht weiterverfolgt

Positive Freigaben werden serverseitig gegen Nutzen, Machbarkeit, Datenreife, Risiko, Governance und erforderliche Fachprüfungen geprüft. Freigaben mit Auflagen benötigen eine zweite unabhängige Bestätigung.

### Bearbeitbare Blocker

Offene Voraussetzungen werden als konkrete Aufgaben dargestellt:

- **Datenblocker** springen zum fehlenden Formularfeld.
- **Prozessblocker** führen zur zuständigen Bewertung, Freigabe oder Governance-Prüfung.

Dashboard, Detailseite und Entscheidungsansicht zeigen Anzahl, Hauptblocker und nächste Aktion.

### Portfolio

Die Portfolio-Sicht enthält:

- kategorische 3×3-Matrix aus wirtschaftlichem Nutzen und technischer Machbarkeit
- Entscheidungsstatus als Farbe
- Confidence als Umrandungsstil
- Filter nach Organisationseinheit, Lifecycle, Status, Lösungstyp und Confidence
- gruppierte Landkarte nach Organisationseinheit, Lösungstyp, Lifecycle oder Status
- separaten Bereich für nicht einordenbare Use Cases
- kontrollierbares Einblenden nicht weiterverfolgter Vorhaben

Es wird kein künstlicher Gesamtscore, kein automatisches Ranking und kein Bubble-Sizing verwendet.

### Delivery

Aus einer final positiven Freigabe kann ein versioniertes **Delivery Package** erzeugt werden.

Es konsolidiert:

- Problem- und Geschäftskontext
- Ziel, Nutzer und Nutzungsszenarien
- In-Scope und Out-of-Scope
- Lösungs-, System-, Daten- und Integrationskontext
- funktionale und nichtfunktionale Anforderungen
- Security-, Datenschutz- und Rechtsanforderungen
- menschliche Aufsicht, Logging, Betrieb und Support
- MVP-Scope
- Akzeptanzkriterien und Testfälle
- Erfolgsmessung
- Risiken, Annahmen und Abhängigkeiten
- Architekturentscheidungen
- initiales Backlog
- Link zum externen Delivery-System

Ein Package durchläuft `Entwurf → Bereit zur Übergabe → Übergeben`. Übergebene Versionen sind unveränderlich; Änderungen erfolgen über eine neue Version. Der Inhalt kann als Markdown exportiert werden.

KI-Radar übernimmt keine Sprint-, Ressourcen- oder Aufgabenplanung. Die operative Umsetzung bleibt im jeweiligen Delivery-System.

## TOGAF-light

KI-Radar nutzt TOGAF ADM als pragmatischen Ordnungsrahmen, nicht als vollständiges Enterprise-Architecture-Repository:

| ADM-Phase | Konkretes KI-Radar-Artefakt |
|---|---|
| A – Architecture Vision | Scope, strategisches Ziel, Stakeholder, Leitplanken, Auslöser und Ergebnis |
| B – Business Architecture | Value Stream, Phasen, Rollen, Ist-Prozess, Regeln, Bottlenecks und Kennzahlen |
| C – Information Systems | Anwendungen, Datenobjekte, Informationsflüsse und Integrationen |
| D – Technology Architecture | Technologie- und Hosting-Leitplanken innerhalb der Lösungsoption |
| E – Opportunities & Solutions | explizite organisatorische, klassische und KI-Lösungsoptionen |
| F – Migration Planning | MVP-Scope, Akzeptanz, Risiken, Abhängigkeiten, Backlog und Delivery Package |
| G/H | Entscheidungen, Versionen und Änderungen werden dokumentiert; kein vollständiges EA-Governance-Modul |

Der TOGAF-Bezug ist nur dort sichtbar, wo tatsächlich entsprechende Artefakte erfasst werden.

## Lifecycle und Nutzenmessung

Operativer Lifecycle:

1. Idee
2. Prüfung
3. Pilot
4. Betrieb
5. Beendet

Jeder bewertungsreife Use Case besitzt eine primäre Erfolgsmetrik mit Baseline, Zielwert, Optimierungsrichtung, Einheit und Messmethode. Für Pilot und Go-live gelten verbindliche Voraussetzungen. Ist-Wert, Messzeitraum, Messdatum und Nachweis machen die Zielerreichung überprüfbar.

## Rollen

| Rolle | Verantwortung |
|---|---|
| Technischer Administrator | Betrieb, Benutzer und Stammdaten |
| KI-Koordinator | übergreifende Analyse, Bewertung, Governance, Freigabe und Delivery-Handover |
| Business Owner | fachliche Verantwortung sowie Pflege eigener Analysen, Use Cases und Package-Entwürfe |
| Leser | lesender Zugriff auf nicht archivierte Inhalte |

Berechtigungen und fachliche Gates werden serverseitig geprüft.

## Optionaler Review-Copilot

Optional kann über OpenRouter ein semantischer Review-Copilot aktiviert werden. Er liefert ausschließlich Hinweise und darf keine Freigabe, Lifecycle-Entscheidung oder rechtliche Klassifizierung vornehmen. Ohne API-Key funktionieren alle verbindlichen Funktionen vollständig.

## Bewusste Nicht-Ziele

KI-Radar ist kein:

- Projektmanagement- oder Ressourcenplanungssystem
- BPMN-Modellierer
- vollständiges Enterprise-Architecture-Repository
- automatisches Priorisierungs- oder Budgetoptimierungssystem
- automatisches AI-Act-Klassifizierungssystem
- Ersatz für Datenschutz-, Rechts- oder Sicherheitsprüfungen
- autonomes LLM-Entscheidungssystem
- Multi-Tenant-SaaS

## Technischer Aufbau

- Python 3.13
- Django 5.2 LTS
- PostgreSQL
- serverseitige Django-Templates und Bootstrap
- modularer Monolith mit separaten Apps für Architecture, Use Cases, Governance, Reporting und Delivery
- Gunicorn und Nginx
- Docker Compose für lokal, Staging und Produktion
- `django-simple-history`
- optional OpenRouter und Sentry

## Schnellstart

```powershell
git clone https://github.com/Satte882/KI-UseCase-Radar.git
cd KI-UseCase-Radar
Copy-Item .env.example .env
docker compose -f compose.local.yml up --build
```

Anwendung:

```text
http://127.0.0.1:8000
```

Demo-Daten und weitere lokale Schritte stehen in [SETUP.md](SETUP.md).

## Qualitätssicherung

Die CI prüft unter anderem:

- Lockfile-Konsistenz
- Ruff Lint und Format
- Django System Check
- fehlende Migrationen
- Unit- und Integrationstests mit PostgreSQL
- Bandit und Dependency Audit
- lokale, Staging- und Produktions-Compose-Konfiguration
- Produktions- und Entwicklungs-Docker-Images

## Dokumentation

- [Discovery & Architecture](docs/DISCOVERY_ARCHITECTURE.md)
- [Lokales Setup](SETUP.md)
- [Betrieb](docs/OPERATIONS.md)
- [Backup und Restore](docs/BACKUP_RESTORE.md)
- [Monitoring](docs/MONITORING.md)
- [Security](docs/SECURITY.md)
- [Architecture Decision Records](docs/adr/)

## Grundprinzip

> KI-Radar bewertet nicht, ob eine Idee modern klingt. Es macht sichtbar, ob ein Vorhaben aus einem relevanten Geschäftsproblem entsteht, messbar, technisch realistisch, ausreichend belegt, verantwortbar entscheidbar und für Delivery konkret genug ist.
