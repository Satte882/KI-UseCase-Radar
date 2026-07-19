# KI-Radar lokal unter Windows 11 mit VS Code starten

Diese Anleitung geht von folgendem Zielpfad aus:

```text
C:\Users\user\Documents\GitHub\KI-UseCase-Radar
```

Der Repository-Name lautet **KI-UseCase-Radar**. Der in der Anfrage einmal genannte Pfad `KI-UseCae-Radar` enthält einen Schreibfehler und wird nicht verwendet.

## 1. Voraussetzungen

Installieren Sie:

1. **Git for Windows**
2. **Visual Studio Code**
3. **Docker Desktop** mit aktivierter WSL-2-Engine
4. optional **Python 3.13** und **uv**, falls Sie ohne App-Container entwickeln möchten

Prüfen Sie in PowerShell:

```powershell
git --version
docker --version
docker compose version
```

## 2. Repository klonen

Öffnen Sie PowerShell:

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

## 4. Administratorkonto anlegen

Öffnen Sie ein zweites Terminal:

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
2. Benutzer anlegen,
3. Benutzer einer der Gruppen zuordnen:
   - Technischer Administrator
   - KI-Koordinator
   - Business Owner
   - Leser
4. bei technischen Administratoren zusätzlich `Mitarbeiter-Status` aktivieren, sofern sie den Django Admin verwenden sollen.

Für einen realistischen Einzeltest können Sie dasselbe Benutzerkonto sowohl als Superuser als auch als KI-Koordinator verwenden.

## 6. Tests ausführen

### Im Docker-Container gegen PostgreSQL

```powershell
docker compose -f compose.local.yml exec app pytest
```

### Qualitätschecks

```powershell
docker compose -f compose.local.yml exec app ruff check .
docker compose -f compose.local.yml exec app python manage.py check
docker compose -f compose.local.yml exec app python manage.py makemigrations --check --dry-run
```

Die Dev-Abhängigkeiten werden im Produktionsimage bewusst nicht installiert. Für lokale Qualitätschecks kann daher alternativ die native `uv`-Variante verwendet werden oder ein Entwicklungsimage gebaut werden. Die GitHub-CI führt alle Qualitätschecks verbindlich aus.

## 7. Native Entwicklung mit uv

Diese Variante verwendet PostgreSQL weiterhin aus Docker, führt Django aber direkt unter Windows aus.

### PostgreSQL starten

```powershell
docker compose -f compose.local.yml up -d db
```

### Virtuelle Umgebung und Abhängigkeiten

```powershell
uv sync --frozen --dev
Copy-Item .env.example .env
```

PowerShell-Umgebungsvariablen für die aktuelle Sitzung setzen:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.dev"
$env:POSTGRES_HOST = "127.0.0.1"
$env:POSTGRES_PORT = "5433"
$env:POSTGRES_DB = "ki_radar"
$env:POSTGRES_USER = "ki_radar"
$env:POSTGRES_PASSWORD = "ki_radar_local"
$env:DJANGO_SECRET_KEY = "local-development-only"
```

Migrationen und Start:

```powershell
uv run python manage.py migrate
uv run python manage.py seed_roles
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Tests:

```powershell
uv run pytest
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
```

## 8. Beispieldaten manuell anlegen

1. Im Admin eine Organisationseinheit anlegen.
2. Auf der Startseite **Use Cases** öffnen.
3. **Use Case anlegen** wählen.
4. Als KI-Koordinator ein Governance-Screening und ein Review hinzufügen.
5. Die Monatsreview-Ansicht öffnen.

## 9. Review-Scan ohne E-Mail

Der aktuelle erste Umsetzungsschritt versendet keine E-Mails. Der tägliche Scan kann manuell ausgeführt werden:

```powershell
docker compose -f compose.local.yml exec app python manage.py scan_due_reviews
```

Der Scan dokumentiert den Lauf im Modell `SystemJobRun`. Fällige und überfällige Reviews werden direkt aus der Datenbank im Dashboard und in der Monatsreview-Ansicht angezeigt.

## 10. Health-Checks

```text
http://127.0.0.1:8000/health/live
http://127.0.0.1:8000/health/ready
```

Der operative Health-Endpunkt benötigt in Produktion einen geheimen Header und ist lokal ohne `MONITORING_TOKEN` absichtlich nicht verfügbar.

## 11. Daten zurücksetzen

Achtung: Dieser Befehl löscht die lokale Docker-Datenbank vollständig.

```powershell
docker compose -f compose.local.yml down -v
```

Anschließend neu starten:

```powershell
docker compose -f compose.local.yml up --build
```

## 12. Häufige Fehler

### Port 8000 ist belegt

In `compose.local.yml` den linken Port ändern, beispielsweise:

```yaml
ports:
  - "127.0.0.1:8010:8000"
```

Dann `http://127.0.0.1:8010` öffnen.

### Port 5433 ist belegt

Den linken Datenbankport ändern. Bei nativer Entwicklung zusätzlich `POSTGRES_PORT` anpassen.

### Docker Desktop läuft nicht

Docker Desktop starten und warten, bis die Engine betriebsbereit ist.

### Migrationen fehlen

```powershell
docker compose -f compose.local.yml exec app python manage.py makemigrations --check --dry-run
```

Es dürfen keine nicht versionierten Modelländerungen vorhanden sein.
