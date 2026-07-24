# KI-Radar

[![KI-Radar CI](https://github.com/Satte882/KI-UseCase-Radar/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Satte882/KI-UseCase-Radar/actions/workflows/ci.yml)

> AI Business Architecture, Portfolio- und Decision-Governance-Cockpit für kleine und mittlere Unternehmen

KI-Radar verbindet die Analyse von Geschäftsprozessen mit der strukturierten Auswahl, Bewertung, Freigabe und Übergabe von KI-Vorhaben an ein Delivery-Team.

Das System beantwortet nicht nur, **welche KI-Ideen existieren**, sondern vor allem:

* Aus welchem Geschäftsproblem entsteht ein Vorhaben?
* Welcher End-to-End-Bereich rechtfertigt überhaupt einen Deep Dive?
* Ist KI tatsächlich die geeignete Lösung?
* Sind Nutzen, Datenlage und technische Machbarkeit ausreichend belegt?
* Welche Governance- und Fachprüfungen fehlen?
* Ist das Vorhaben entscheidungs- und umsetzungsreif?
* Welche Systeme, Datenflüsse und Architekturartefakte benötigt Delivery?

---

## End-to-End-Arbeitsmodell

```text
Discovery
→ Fokus & Priorisierung
→ Use Cases
→ Bewertung
→ Freigabe
→ Delivery
```

Der systematische Architecture-Pfad wird detaillierter so umgesetzt:

```text
Fachdomäne und Business Capability
→ End-to-End-Value-Stream
→ transparentes Fokus-Screening
→ Auswahl für einen Prozess-Deep-Dive
→ organisatorische, klassische und KI-Lösungsoptionen
→ geführter Use-Case-Intake
→ evidenzbasierte Bewertung
→ verbindliche Freigabe
→ versioniertes Delivery Package
→ Umsetzung in Jira, Azure DevOps, GitHub oder einem anderen Delivery-System
```

Die Gesamtstrecke bleibt in der Oberfläche dauerhaft sichtbar. Auf Detailseiten zeigt sie den tatsächlichen Zustand einer Initiative; die linke Navigation öffnet zusätzlich die lokale Tiefe des aktiven Bereichs.

Der Discovery- und Architecture-Pfad bleibt optional. Bereits bekannte Vorhaben können direkt über den Use-Case-Intake erfasst werden. Systematisch abgeleitete Vorhaben erhalten zusätzlich eine nachvollziehbare Herkunftskette vom Value Stream über die Fokusentscheidung und Lösungsoption bis zum Use Case.

Portfolio ist kein einmaliger linearer Schritt. Es ist eine Querschnittssicht über Use Cases, Bewertung, Freigabe und Delivery.

---

## Welches Problem löst KI-Radar?

In vielen Organisationen sind Informationen über KI-Ideen, Prozessprobleme, Priorisierungsentscheidungen, Bewertungen, Governance-Prüfungen und Delivery-Anforderungen über Tabellen, Präsentationen, Tickets und einzelne Dokumente verteilt.

Dadurch bleiben zentrale Fragen häufig unbeantwortet:

* Wo entsteht im End-to-End-Prozess ein relevantes Problem?
* Welcher Value Stream oder Prozessbereich sollte zuerst vertieft werden?
* Wie hoch ist der erwartete und messbare Nutzen?
* Welche einfacheren Lösungsalternativen wurden geprüft?
* Wie belastbar sind Machbarkeit, Datenlage und Risiken bewertet?
* Welche Entscheidung wurde wann, von wem und auf welcher Evidenzbasis getroffen?
* Welche Vorhaben gehören aktiv ins Portfolio?
* Welche Voraussetzungen fehlen noch?
* Ist der Scope einschließlich Systemlandschaft und Architekturkontext konkret genug für Delivery?

KI-Radar führt diese Informationen in einem gemeinsamen, nachvollziehbaren Arbeitsmodell zusammen.

---

## Vier zentrale Produktfähigkeiten

### 1. Business Architecture, Discovery und Fokus

KI-Radar unterstützt die strukturierte Analyse eines Geschäftsbereichs durch:

* kontrollierte Fachdomänen und Business Capabilities
* End-to-End-Value-Streams
* geordnete Wertschöpfungsphasen
* Rollen, Systeme und Dokumente
* Probleme, Engpässe und Baseline-Kennzahlen
* Fokus-Screening nach strategischem Impact, wirtschaftlichem Potenzial, Problemintensität, Datenzugänglichkeit und Veränderungsaufwand
* dokumentierte Auswahl für einen Deep Dive
* detaillierte Prozessanalysen
* organisatorische, regelbasierte und technische Lösungsoptionen

Nur ein vollständig bewerteter und ausgewählter Value Stream darf neue Prozess-Deep-Dives, bevorzugte Lösungsoptionen oder systematisch abgeleitete Use Cases starten. Dieses Gate wird serverseitig geprüft.

KI wird nicht automatisch als bevorzugte Lösung behandelt. Eine organisatorische Änderung, Standardsoftware oder regelbasierte Automatisierung kann die bessere Option sein.

### 2. Decision Governance

Jeder Use Case wird anhand einer nachvollziehbaren Evidenzbasis bewertet.

Berücksichtigt werden unter anderem:

* wirtschaftlicher Nutzen
* strategischer Beitrag
* technische Machbarkeit
* Datenreife
* Risiko und Komplexität
* Qualität und Aktualität der Evidenz
* unabhängige Prüfung
* offene Annahmen
* Governance- und Fachprüfungen

Bewertung und Freigabe sind getrennte Arbeitsschritte.

Verbindliche Entscheidungen werden serverseitig durch deterministische Hard Gates abgesichert. Ein optionales LLM kann Hinweise liefern, aber keine Freigabe oder Lifecycle-Entscheidung auslösen.

### 3. Portfolio-Steuerung

Die Portfolio-Sicht verbindet Managementübersicht und operative Handlungsfähigkeit:

* Fachdomänen- und Capability-Zuordnung unabhängig von der Organisationseinheit
* kategorische Matrix aus Nutzen und technischer Machbarkeit
* Entscheidungsstatus und Confidence
* Filter nach Organisationseinheit, Lifecycle, Lösungstyp und Status
* gruppierte Portfolio-Landkarte
* separate Darstellung nicht einordenbarer Vorhaben
* konkrete Daten- und Prozessblocker
* direkte Navigation zur jeweils notwendigen Aktion

Es wird bewusst kein künstlicher Gesamtscore und kein automatisches Ranking verwendet. Die Kriterien und ihre Evidenz bleiben einzeln sichtbar.

### 4. Delivery Readiness

Aus einer final positiven Freigabe kann ein versioniertes Delivery Package erzeugt werden.

Es bündelt:

* Problem- und Geschäftskontext
* Zielbild
* In-Scope und Out-of-Scope
* Nutzer und Nutzungsszenarien
* System-, Daten- und Integrationskontext
* Ist-/Ziel-Systemlandschaft
* Daten- und Informationsflüsse
* Integrationsverträge und technische Verantwortlichkeiten
* Link zu Architekturdiagrammen und weiteren Architekturartefakten
* funktionale und nichtfunktionale Anforderungen
* Security-, Datenschutz- und Rechtsanforderungen
* Human Oversight, Logging, Betrieb und Support
* MVP-Scope
* Akzeptanzkriterien und Testfälle
* Erfolgsmessung
* Risiken, Annahmen und Abhängigkeiten
* Architekturentscheidungen und Leitplanken
* initiales Backlog
* Link zum externen Delivery-System

Für den Status **Bereit zur Übergabe** müssen Architektur- und Übergabepunkte konkret beschrieben oder ausdrücklich als nicht relevant dokumentiert sein. Leere Integrationen, Abhängigkeiten, Risiken, Annahmen oder Architekturentscheidungen gelten nicht automatisch als ausreichend.

Delivery Readiness 2.0 gliedert das Package in sieben prüfbare Sektionen. Automatisch übernommene Inhalte bleiben als Herkunft sichtbar und müssen fachlich beziehungsweise technisch bestätigt werden. Strukturierte Readiness-Findings benennen konkrete Blocker; die Prüfung wird vor der verbindlichen Übergabe erneut serverseitig ausgeführt.

Die vollständige methodische Grundlage ist im [Vorgehensmodell für produktionsreife KI-Systeme](docs/DELIVERY_METHODOLOGY.md) hinterlegt. In-App-Ansicht und Markdown-Download verwenden dieselbe versionierte Datei; KI-Radar führt dadurch keinen zusätzlichen CRISP-ML(Q)-Workflow und keine automatische ML-Test-Score-Berechnung ein.

Der Status verläuft über:

```text
Entwurf → Bereit zur Übergabe → Übergeben
```

Übergebene Versionen sind unveränderlich. Änderungen erfolgen über eine neue Version.

---

## Beispiel: Automatische Eingangsrechnungsprüfung

Der mitgelieferte Demo-Datensatz zeigt den vollständigen Arbeitsablauf:

1. Der Value Stream **„Beschaffung bis Zahlung“** wird der Fachdomäne Finanzen und der Capability Accounts Payable zugeordnet.
2. Das Fokus-Screening dokumentiert Impact, wirtschaftliches Potenzial, Problemintensität, Datenzugänglichkeit und Veränderungsaufwand.
3. Der Value Stream wird nachvollziehbar für einen Deep Dive ausgewählt.
4. Die Prozessanalyse identifiziert manuelle Suche, Medienbrüche und Rückfragen als Bottlenecks.
5. Organisatorische, regelbasierte und KI-gestützte Lösungsoptionen werden verglichen.
6. Eine kombinierte Regel- und Assistenzlösung wird als bevorzugte Option gewählt.
7. Der daraus abgeleitete Use Case wird hinsichtlich Nutzen, Datenreife, Machbarkeit, Risiko und Governance bewertet.
8. Nach der finalen Freigabe entsteht ein versioniertes Delivery Package mit Systemlandschaft, Datenflüssen, MVP-Scope, Anforderungen und Akzeptanzkriterien.
9. Das Delivery Package ist bereit für die verbindliche Übergabe an ein externes Delivery-System, aber noch nicht als übergeben markiert.

Damit wird nicht nur ein KI-Use-Case dokumentiert, sondern seine fachliche Herkunft, Auswahlentscheidung und Umsetzungsreife nachvollziehbar gemacht.

---

## TOGAF-light

KI-Radar nutzt TOGAF ADM als pragmatischen Ordnungsrahmen. Es ist kein vollständiges Enterprise-Architecture-Repository und bildet kein umfassendes TOGAF-Metamodell ab.

| Bereich                   | Umsetzung in KI-Radar                                                      |
| ------------------------- | -------------------------------------------------------------------------- |
| Architecture Vision       | Scope, Ziel, Stakeholder und Leitplanken                                   |
| Business Architecture     | Fachdomäne, Capability, Value Streams, Prozesse, Rollen und Bottlenecks    |
| Information Systems       | Anwendungen, Datenobjekte, Datenflüsse und Integrationen                   |
| Technology Architecture   | Technologie-, Hosting- und Plattformbedingungen                            |
| Opportunities & Solutions | Fokusentscheidung sowie organisatorische, klassische und KI-Optionen       |
| Migration Planning        | Systemlandschaft, MVP, Akzeptanz, Risiken, Backlog und Delivery Package    |
| Governance und Change     | Entscheidungen, Versionen und Änderungen                                   |

Der TOGAF-Bezug wird nur dort verwendet, wo tatsächlich entsprechende Architekturartefakte entstehen.

Details: [Discovery & Architecture](docs/DISCOVERY_ARCHITECTURE.md)

---

## Architekturübersicht

```text
Browser
   │
   ▼
Django Modular Monolith
   ├── Architecture
   ├── Use Cases
   ├── Governance
   ├── Reviews
   ├── Reporting
   ├── Delivery
   └── Accounts
   │
   ▼
PostgreSQL
```

Optionale externe Systeme:

```text
OpenRouter · Sentry · Jira · Azure DevOps · GitHub · Confluence
```

KI-Radar bleibt fachlich und technisch ein klar abgegrenztes System:

* Analyse und Entscheidung verbleiben in KI-Radar.
* Die operative Delivery-Steuerung verbleibt in spezialisierten Werkzeugen.
* Verbindliche Prüfungen werden serverseitig ausgeführt.
* LLM-Funktionen sind optional und nicht entscheidungsbefugt.
* Die Systemlandschaft im Delivery Package ist eine umsetzungsbezogene Ist-/Ziel-Sicht, kein vollständiger Enterprise-Architecture-Katalog.

---

## Datenspeicherung

Fachliche Eingaben aus der Weboberfläche werden nach erfolgreicher Validierung in PostgreSQL gespeichert. Git und GitHub enthalten Code, Migrationen und Dokumentation, aber nicht automatisch die erfassten Use Cases, Bewertungen, Governance-Screenings, Reviews oder Delivery Packages.

Im lokalen Docker-Setup liegen die PostgreSQL-Daten persistent im Volume `local_db`. Ein normaler Container-Neustart, Rebuild oder Branchwechsel lässt dieses Volume bestehen. `docker compose -f compose.local.yml down -v` löscht dagegen die lokale Datenbank und alle lokalen Volumes vollständig.

Ohne konfigurierten API-Key werden keine Use-Case-Daten an OpenRouter gesendet. Erst eine ausdrücklich gestartete Copilot-Analyse überträgt ausgewählte Daten an die konfigurierte API.

Details zu Datenarten, Änderungshistorie, Nachweislinks, lokalen und produktiven Volumes, Backups, Löschung und optionalen externen Übertragungen stehen in [Datenspeicherung und Datenfluss](docs/DATA_STORAGE.md).

## Zentrale Architekturentscheidungen

Architekturentscheidungen werden als Architecture Decision Records dokumentiert. Sie halten nicht nur das Ergebnis, sondern auch Kontext, Trade-offs und Konsequenzen einer Entscheidung fest.

### Dokumentierte ADRs

| ADR                                           | Entscheidung                                                                  | Begründung                                                               |
| --------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| [0001](docs/adr/0001-django-monolith.md)      | Modularer Django-Monolith                                                     | geringe Deployment-, Authentifizierungs- und Berechtigungskomplexität    |
| [0002](docs/adr/0002-history.md)              | Technische Historie und fachliche Entscheidungen werden getrennt dokumentiert | Auditierbarkeit ohne Vermischung von Datenänderung und Freigabe          |
| [0003](docs/adr/0003-staging-same-host.md)    | Staging als separater Stack auf demselben Host                                | wirtschaftlicher Einzelbetrieb bei logischer Trennung                    |
| [0004](docs/adr/0004-no-email-reminders.md)   | Noch kein produktiver E-Mail-Versand                                          | keine Anbieter- und Eskalationslogik ohne konkreten Betrieb vorwegnehmen |
| [0005](docs/adr/0005-anonymization-ledger.md) | Restore-feste Anonymisierung über ein externes Ledger                         | spätere Backups dürfen Anonymisierungen nicht rückgängig machen          |

### Weitere prägende Produktentscheidungen

* Discovery bleibt optional und belastet bekannte Einzelvorhaben nicht mit unnötigen Architekturartefakten.
* Der systematische Architecture-Pfad verlangt eine dokumentierte Fokusentscheidung vor dem Deep Dive.
* Organisationseinheit und fachliche Domäne werden getrennt modelliert.
* KI ist eine Lösungsoption unter mehreren und wird nicht automatisch bevorzugt.
* Freigaben beruhen auf deterministischen Hard Gates, nicht auf LLM-Ausgaben.
* Portfolio ist eine Querschnittssicht und kein linearer Prozessschritt.
* Fokus- und Portfolio-Entscheidungen verwenden keine künstliche Gesamtnote.
* Delivery Packages werden erst nach finaler Freigabe erzeugt.
* Übergebene Package-Versionen sind unveränderlich.
* KI-Radar ersetzt kein Projektmanagement- oder Delivery-System.

---

## Rollen

| Rolle                     | Verantwortung                                                                  |
| ------------------------- | ------------------------------------------------------------------------------ |
| Technischer Administrator | Betrieb, Benutzer und Stammdaten                                               |
| KI-Koordinator            | Fokus, Analyse, Bewertung, Governance, Freigaben und Delivery-Handover         |
| Business Owner            | fachliche Verantwortung für Value Streams, Prozesse, Use Cases und Packages    |
| Leser                     | lesender Zugriff auf nicht archivierte Inhalte                                 |

Berechtigungen und fachliche Gates werden serverseitig geprüft.

---

## Bewusste Nicht-Ziele

KI-Radar ist kein:

* Projektmanagement- oder Ressourcenplanungssystem
* BPMN-Modellierer
* vollständiges Enterprise-Architecture-Repository
* automatisches Priorisierungs- oder Budgetoptimierungssystem
* automatisches AI-Act-Klassifizierungssystem
* Ersatz für Datenschutz-, Rechts- oder Sicherheitsprüfungen
* autonomes LLM-Entscheidungssystem
* Multi-Tenant-SaaS

Der Schwerpunkt liegt auf der fachlich begründeten Auswahl, belastbaren Entscheidung und strukturierten Übergabe von KI-Vorhaben.

---

## Technischer Aufbau

* Python 3.13
* Django 5.2 LTS
* PostgreSQL
* serverseitige Django-Templates
* Bootstrap
* modularer Monolith
* Gunicorn und Nginx
* Docker Compose für lokale Entwicklung, Staging und Produktion
* `django-simple-history`
* optional OpenRouter
* optional Sentry

---

## Qualitätssicherung

Die CI prüft unter anderem:

* Lockfile-Konsistenz
* Ruff Lint und Format
* Django System Check
* fehlende Migrationen
* Unit- und Integrationstests mit PostgreSQL
* Berechtigungen und serverseitige Hard Gates
* Security-Prüfung mit Bandit
* Dependency Audit
* lokale, Staging- und Produktionskonfiguration
* Produktions- und Entwicklungs-Docker-Images

Die automatisierten Tests decken insbesondere ab:

* Value Streams, Fokus-Screening und Prozessanalysen
* serverseitige Deep-Dive-Gates
* Lösungsoptionen und Herkunftsketten
* strukturierte Fachdomänen und Capabilities
* Use-Case-Intake
* Bewertungen und Freigaben
* Governance
* Lifecycle-Übergänge
* Portfolio
* Delivery Packages und Architekturartefakte
* Rollen und Berechtigungen
* Anonymisierung
* Demo-Daten und Betriebsfunktionen

---

## Schnellstart

### Voraussetzungen

* Git
* Docker Desktop beziehungsweise Docker Engine
* Docker Compose

### Anwendung starten

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

### Demo-Daten anlegen

```powershell
docker compose -f compose.local.yml exec app `
  python manage.py seed_demo_data --password "<lokales-demo-passwort>"
```

Der Demo-Datensatz enthält einen vollständigen Ablauf von Discovery und Fokusentscheidung bis zum Delivery Package sowie bewusst unvollständige, nicht weiterverfolgte und bereits übergebene Szenarien.

Weitere Informationen: [Lokales Setup](SETUP.md)

---

## Reifegrad und Einsatzgrenzen

KI-Radar ist eine funktionsfähige Single-Tenant-Referenzimplementierung für den internen Einsatz in einer Organisation.

Vor einer extern erreichbaren Produktivinstallation müssen abhängig vom konkreten Unternehmen insbesondere geklärt werden:

* Unternehmens-SSO und MFA
* Domain, DNS und TLS
* E-Mail- und Eskalationskanäle
* externes Monitoring und Alarmierung
* Offsite-Backups
* Datenschutz- und Aufbewahrungsvorgaben
* Lizenz- und Betriebsmodell

Ohne SSO sollte der Zugriff auf ein internes Netz oder VPN beschränkt bleiben.

---

## Dokumentation

* [Marktvalidierung und Continue/Pivot/Stop](docs/VALIDATION_PLAN.md)
* [Baseline-Abschluss und KI-beschleunigte Delivery](docs/AI_ACCELERATION_PLAN.md)
* [Discovery & Architecture](docs/DISCOVERY_ARCHITECTURE.md)
* [Lokales Setup](SETUP.md)
* [Datenspeicherung und Datenfluss](docs/DATA_STORAGE.md)
* [Security](docs/SECURITY.md)
* [Betrieb](docs/OPERATIONS.md)
* [Backup und Restore](docs/BACKUP_RESTORE.md)
* [Monitoring](docs/MONITORING.md)
* [Architecture Decision Records](docs/adr/)
* [Offene Betriebs- und Konfigurationsentscheidungen](OPEN_QUESTIONS.md)

---

## Grundprinzip

> KI-Radar bewertet nicht, ob eine Idee modern klingt.
> Es macht sichtbar, ob ein Vorhaben aus einem relevanten Geschäftsproblem entsteht, priorisiert vertieft werden sollte, messbar, technisch realistisch, ausreichend belegt, verantwortbar entscheidbar und für Delivery einschließlich Architekturkontext konkret genug ist.
