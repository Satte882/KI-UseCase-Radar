# KI-Radar lokal unter Windows 11 mit VS Code starten

Diese Anleitung verwendet folgenden Zielpfad:

```text
C:\Users\user\Documents\GitHub\KI-UseCase-Radar
```

Der Repository-Name lautet **KI-UseCase-Radar**. Der einmal genannte Ordnername `KI-UseCae-Radar` enthält einen Schreibfehler und wird nicht verwendet.

## 1. Voraussetzungen

Erforderlich sind:

1. **Git for Windows**
2. **Visual Studio Code**
3. **Docker Desktop** mit aktivierter WSL-2-Engine

Optional für eine native Python-Entwicklung:

4. **Python 3.13**
5. **uv 0.10.x**

In PowerShell prüfen:

```powershell
git --version
docker --version
docker compose version
```

Docker Desktop muss gestartet sein, bevor der lokale Stack ausgeführt wird.

## 2. Repository klonen

In PowerShell:

```powershell
cd C:\Users\user\Documents\GitHub
git clone https://github.com/Satte882/KI-UseCase-Radar.git
cd KI-UseCase-Radar
code .
```

Für spätere Aktualisierungen:

```powershell
git fetch origin
git pull --ff-only origin main
```

## 3. Empfohlener Start mit Docker Compose

Im integrierten VS-Code-Terminal:

```powershell
docker compose -f compose.local.yml up --build
```

Der lokale Stack verwendet `Dockerfile.dev`. Dieses Entwicklungsimage enthält neben den Laufzeitabhängigkeiten auch Pytest, Ruff, Bandit und pip-audit. Das separate Produktionsimage aus `Dockerfile` bleibt davon unberührt und enthält keine Entwicklungswerkzeuge.

Beim ersten Start werden automatisch:

- PostgreSQL gestartet,
- Datenbankmigrationen ausgeführt,
- die vier Rollen angelegt,
- statische Dateien gesammelt,
- der Django-Entwicklungsserver gestartet.

Die Anwendung ist erreichbar unter:

```text
http://127.0.0.1:8000
```

Der Prozess bleibt im Terminal aktiv. Beenden mit `Strg+C`.

## 4. Administratorkonto anlegen

Ein zweites VS-Code-Terminal öffnen:

```powershell
docker compose -f compose.local.yml exec app python manage.py createsuperuser
```

Danach anmelden unter:

```text
http://127.0.0.1:8000/accounts/login/
```

Die technische Administration ist erreichbar unter:

```text
http://127.0.0.1:8000/admin/
```

## 5. Erste fachliche Konfiguration

Im Django Admin:

1. mindestens eine **Organisationseinheit** anlegen,
2. benötigte Benutzer anlegen,
3. Benutzer einer oder mehreren Gruppen zuordnen:
   - Technischer Administrator
   - KI-Koordinator
   - Business Owner
   - Leser
4. für Benutzer mit Django-Admin-Zugriff zusätzlich `Mitarbeiter-Status` aktivieren.

Für den aktuellen Einzelbetrieb kann dasselbe Konto Superuser und KI-Koordinator sein.

## 6. Lokale Qualitätsprüfungen

Der lokale Docker-Stack enthält alle Entwicklungsabhängigkeiten.

```powershell
docker compose -f compose.local.yml exec app pytest
docker compose -f compose.local.yml exec app ruff check .
docker compose -f compose.local.yml exec app python manage.py check
docker compose -f compose.local.yml exec app python manage.py makemigrations --check --dry-run
docker compose -f compose.local.yml exec app bandit -q -r ki_radar config
docker compose -f compose.local.yml exec app pip-audit
```

Den Produktionscontainer lokal bauen:

```powershell
docker build -t ki-radar:local .
```

## 7. Native Entwicklung mit uv

Diese Variante startet nur PostgreSQL in Docker und führt Django direkt unter Windows aus.

### PostgreSQL starten

```powershell
docker compose -f compose.local.yml up -d db
```

### Abhängigkeiten installieren

```powershell
uv sync --frozen --dev
Copy-Item .env.example .env
```

Umgebungsvariablen für die aktuelle PowerShell-Sitzung:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.dev"
$env:POSTGRES_HOST = "127.0.0.1"
$env:POSTGRES_PORT = "5433"
$env:POSTGRES_DB = "ki_radar"
$env:POSTGRES_USER = "ki_radar"
$env:POSTGRES_PASSWORD = "ki_radar_local"
$env:DJANGO_SECRET_KEY = "local-development-only"
```

Migrationen, Rollen und Administratorkonto:

```powershell
uv run python manage.py migrate
uv run python manage.py seed_roles
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Qualitätsprüfungen:

```powershell
uv run pytest
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run bandit -q -r ki_radar config
uv run pip-audit
```

## 8. Erste Beispieldaten

1. Im Admin eine Organisationseinheit anlegen.
2. Auf der Startseite **Use Cases** öffnen.
3. **Use Case anlegen** wählen.
4. Pflichtinformationen für die Phase „Idee“ eintragen.
5. Als KI-Koordinator ein Governance-Screening anlegen.
6. Über ein Review den Lifecycle-Status verändern.
7. Dashboard und Monatsreview-Ansicht prüfen.

## 9. Review-Scan ohne E-Mail

Im ersten Umsetzungsschritt werden bewusst keine E-Mails versendet. Der Review-Scan kann manuell ausgeführt werden:

```powershell
docker compose -f compose.local.yml exec app python manage.py scan_due_reviews
```

Der Lauf wird in `SystemJobRun` dokumentiert. Fällige und überfällige Reviews werden unabhängig davon direkt aus der Datenbank im Dashboard und in der Monatsreview-Ansicht angezeigt.

## 10. Health-Checks

```text
http://127.0.0.1:8000/health/live
http://127.0.0.1:8000/health/ready
```

Der operative Monitoring-Endpunkt benötigt in Produktion einen geheimen Header. Ohne gesetztes `MONITORING_TOKEN` ist er lokal absichtlich nicht verfügbar.

## 11. Lokale Datenbank sichern und wiederherstellen

Backup erzeugen:

```powershell
docker compose -f compose.local.yml exec db pg_dump -U ki_radar -d ki_radar -Fc -f /tmp/ki-radar.dump
docker compose -f compose.local.yml cp db:/tmp/ki-radar.dump .\ki-radar.dump
```

Für einen Restore-Test eine separate Datenbank verwenden; die produktive beziehungsweise reguläre lokale Datenbank nicht überschreiben. Das vollständige Betriebsverfahren steht in `docs/BACKUP_RESTORE.md`.

## 12. Lokale Daten vollständig zurücksetzen

**Achtung:** Dieser Befehl löscht die lokale Docker-Datenbank und das lokale Anonymisierungs-Ledger.

```powershell
docker compose -f compose.local.yml down -v
```

Anschließend neu starten:

```powershell
docker compose -f compose.local.yml up --build
```

## 13. Häufige Fehler

### Port 8000 ist belegt

In `compose.local.yml` den linken Port ändern, beispielsweise:

```yaml
ports:
  - "127.0.0.1:8010:8000"
```

Danach `http://127.0.0.1:8010` öffnen.

### Port 5433 ist belegt

Den linken Datenbankport in `compose.local.yml` ändern. Bei nativer Entwicklung zusätzlich `POSTGRES_PORT` anpassen.

### Docker Desktop läuft nicht

Docker Desktop starten und warten, bis die Engine betriebsbereit ist.

### Lockfile passt nicht zu pyproject.toml

```powershell
uv lock
uv sync --frozen --dev
```

Eine beabsichtigte Änderung von `uv.lock` muss gemeinsam mit `pyproject.toml` committed werden.

### Migrationen fehlen

```powershell
docker compose -f compose.local.yml exec app python manage.py makemigrations --check --dry-run
```

Es dürfen keine nicht versionierten Modelländerungen vorhanden sein.

### Anwendung startet nach einem Codewechsel nicht

```powershell
docker compose -f compose.local.yml down
docker compose -f compose.local.yml up --build
```
