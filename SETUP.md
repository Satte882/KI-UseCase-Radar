# KI-Radar lokal starten

## 1. Voraussetzungen

- Git for Windows
- Visual Studio Code
- Docker Desktop mit aktivierter WSL-2-Engine

Optional für native Entwicklung: Python 3.13 und uv 0.10.x.

## 2. Repository aktualisieren

```powershell
cd C:\Users\user\Documents\GitHub\KI-UseCase-Radar
git fetch origin
git pull --ff-only origin main
```

Bei einer Erstinstallation:

```powershell
cd C:\Users\user\Documents\GitHub
git clone https://github.com/Satte882/KI-UseCase-Radar.git
cd KI-UseCase-Radar
code .
```

## 3. Lokale Konfiguration und OpenRouter

Falls noch keine `.env` vorhanden ist:

```powershell
Copy-Item .env.example .env
```

Für den optionalen semantischen Review-Copilot in `.env` eintragen:

```dotenv
OPENROUTER_API_KEY=<eigener-key>
```

Optional kann ein konkretes OpenRouter-Modell gewählt werden:

```dotenv
OPENROUTER_MODEL=anbieter/modell-slug
```

Bleibt `OPENROUTER_MODEL` leer, verwendet OpenRouter das im Konto konfigurierte Standardmodell. Ohne API-Key funktionieren alle verbindlichen Decision-Readiness-Checks; nur die semantische Copilot-Analyse ist deaktiviert.

Die `.env` ist durch `.gitignore` vom Repository ausgeschlossen und darf nicht committed werden.

## 4. Anwendung mit Docker starten

```powershell
docker compose -f compose.local.yml up --build
```

Docker Compose liest die `.env` im Repository-Stamm automatisch und reicht die
OpenRouter-Variablen an den App-Container weiter.

Beim Start werden automatisch:

- PostgreSQL gestartet,
- alle Migrationen ausgeführt,
- die vier Rollen angelegt,
- statische Dateien gesammelt,
- der Django-Entwicklungsserver gestartet.

Anwendung:

```text
http://127.0.0.1:8000
```

## 5. Demo-Daten für den Produkttest

Ein zweites Terminal öffnen:

```powershell
docker compose -f compose.local.yml exec app python manage.py seed_demo_data --password "Demo-Test-2026!"
```

Anmeldung als KI-Koordinator:

```text
Benutzer: demo_ki_koordinator
Passwort: Demo-Test-2026!
```

Der Demo-Datensatz enthält Lifecycle-Fälle, Governance-Screenings, Reviews und strukturierte Erfolgsmetriken mit erreichten und verfehlten Zielen. Dadurch können Entscheidungswarteschlange, Pilot-Gates, Go-live-Prüfung und OpenRouter-Copilot direkt getestet werden.

Demo-Daten entfernen:

```powershell
docker compose -f compose.local.yml exec app python manage.py clear_demo_data
```

## 6. Eigenes Administratorkonto

```powershell
docker compose -f compose.local.yml exec app python manage.py createsuperuser
```

Danach:

```text
http://127.0.0.1:8000/accounts/login/
http://127.0.0.1:8000/admin/
```

Im Admin mindestens eine Organisationseinheit und die benötigten Benutzer anlegen. Benutzer werden einer oder mehreren Gruppen zugeordnet:

- Technischer Administrator
- KI-Koordinator
- Business Owner
- Leser

## 7. Fachlicher Testablauf

1. Entscheidungswarteschlange auf der Startseite prüfen.
2. Einen Use Case in der Phase Prüfung öffnen.
3. Primäre Erfolgsmetrik mit Baseline, Ziel, Einheit und Messmethode erfassen.
4. Governance-Screening anlegen.
5. Pilotstart über einen Review beschließen.
6. Ist-Wert, Messzeitraum, Messdatum und Nachweis ergänzen.
7. Go-live-Prüfung öffnen und Zielerreichung kontrollieren.
8. Bei verfehltem Ziel die explizite Ausnahmebestätigung testen.
9. Auf der Detailseite die optionale OpenRouter-Analyse starten.

Der OpenRouter-Copilot liefert ausschließlich semantische Hinweise. Er darf keinen Lifecycle-Übergang freigeben oder blockieren.

## 8. Qualitätsprüfungen

```powershell
docker compose -f compose.local.yml exec app pytest
docker compose -f compose.local.yml exec app ruff check .
docker compose -f compose.local.yml exec app ruff format --check .
docker compose -f compose.local.yml exec app python manage.py check
docker compose -f compose.local.yml exec app python manage.py makemigrations --check --dry-run
docker compose -f compose.local.yml exec app bandit -q -r ki_radar config
docker compose -f compose.local.yml exec app pip-audit
```

Produktionscontainer lokal bauen:

```powershell
docker build -t ki-radar:local .
```

## 9. Native Entwicklung mit uv

Bei der nativen Ausführung lädt Django die `.env` nicht automatisch. Zuerst nur
PostgreSQL starten und die Python-Abhängigkeiten synchronisieren:

```text
docker compose -f compose.local.yml up -d db
uv sync --frozen --dev
```

Die `.env.example` verwendet für die native Verbindung den Host-Port `5433`.
Unter Linux und macOS die Prozessumgebung so laden:

```bash
cp .env.example .env  # nur falls noch keine .env vorhanden ist
set -a
source .env
set +a

uv run python manage.py migrate
uv run pytest -q
uv run python manage.py runserver
```

Unter PowerShell die Einträge sicher zeilenweise in die Prozessumgebung laden:

```powershell
$envFile = ".env"
Get-Content -LiteralPath $envFile | ForEach-Object {
    $line = $_.Trim()

    if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
        $name, $value = $line -split "=", 2

        if ($name) {
            [Environment]::SetEnvironmentVariable(
                $name.Trim(),
                $value,
                "Process"
            )
        }
    }
}

uv run python manage.py migrate
uv run python manage.py seed_roles
uv run pytest -q
uv run python manage.py runserver
```

Für den optionalen Copilot genügt in der `.env`:

```dotenv
OPENROUTER_API_KEY=<eigener-key>
```

## 10. Health-Checks

```text
http://127.0.0.1:8000/health/live
http://127.0.0.1:8000/health/ready
```

## 11. Lokale Daten vollständig zurücksetzen

**Achtung:** Löscht die lokale Datenbank und lokale Volumes.

```powershell
docker compose -f compose.local.yml down -v
docker compose -f compose.local.yml up --build
```

## 12. Häufige Fehler

### OpenRouter-Schaltfläche ist deaktiviert

Prüfen, ob `OPENROUTER_API_KEY` in `.env` gesetzt wurde. Anschließend den App-Container neu starten:

```powershell
docker compose -f compose.local.yml up -d --force-recreate app
```

### Anwendung startet nach einem Codewechsel nicht

```powershell
docker compose -f compose.local.yml down
docker compose -f compose.local.yml up --build
```

### Migrationen fehlen

```powershell
docker compose -f compose.local.yml exec app python manage.py makemigrations --check --dry-run
```

### Port 8000 oder 5433 ist belegt

In `compose.local.yml` den linken Host-Port ändern. Der Container-Port bleibt unverändert.
