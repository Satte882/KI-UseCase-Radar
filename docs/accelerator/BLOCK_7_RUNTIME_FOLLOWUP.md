# Accelerator Block 7 – Runtime-Nachtrag

## Anlass

Beim manuellen Test der produktiven Block-7-Oberfläche traten vier Laufzeitbeobachtungen auf:
Ausgabeabbruch durch Tokenlimit, ein anschließender Running-Hinweis, ein früh erreichtes
Prozesskontingent und die gleichzeitige Anzeige des bestehenden Vergleichsblockers
„Mindestens zwei unterschiedliche Lösungsoptionen sind erforderlich.“

Der Nachtrag bleibt vollständig innerhalb von Block 7. Block 8 wird fachlich nicht berührt.

## 1. Ausgabeabbruch

### Ursache

Der Block-7-Aufruf verwendete bisher das gemeinsame Accelerator-Ausgabelimit von 4096 Tokens.
Das ist für ein Bundle aus drei Optionen mit jeweils zehn Feldern strukturell knapp: Insgesamt
müssen 30 Statements inklusive Text, Source-IDs, Annahmen, offener Evidenz und
Unsicherheitsbegründung in einem einzigen JSON-Dokument erzeugt werden. Der beobachtete
`finish_reason=length` bestätigt, dass das Limit real erreicht wurde.

### Korrektur

Block 7 erhält ein eigenes Ausgabelimit
`ACCELERATOR_SOLUTION_GENERATION_MAX_OUTPUT_TOKENS` mit Default 8192 Tokens und zulässigem
Bereich 4096 bis 16384. Das gemeinsame 4096-Token-Limit für kompaktere Accelerator-Aufrufe
bleibt unverändert. Damit wird nicht pauschal das Kostenbudget aller LLM-Pfade vergrößert.

## 2. Running-Lock

### Ursache

Für den bekannten `finish_reason=length`-Pfad wurde der Run bereits vorher korrekt auf `FAILED`
gesetzt. Ein unmittelbar danach gestarteter neuer Request ist daher zulässig. Der
„läuft bereits“-Hinweis ist erwartbar, wenn ein vorheriger HTTP-/Provider-Aufruf zu diesem
Zeitpunkt tatsächlich noch läuft.

Es bestand jedoch eine Robustheitslücke: Für einen unerwartet abgebrochenen Serverpfad gab es
keine Lease-/Recovery-Regel für einen dauerhaft auf `RUNNING` verbliebenen Datensatz.

### Korrektur

Ein `RUNNING`-Run gilt nach Provider-Timeout plus 15 Sekunden Sicherheitsabstand als verwaist.
Beim nächsten Start wird ein solcher Run atomar als `FAILED` mit
`stale_running_recovered` beendet; erst danach darf ein neuer Run beginnen. Zusätzlich beendet
der Orchestrator unerwartete Exceptions fail-closed mit `internal_error`. Ein verspätet
zurückkehrender superseded Providerlauf kann anschließend keinen erfolgreichen Preview mehr
persistieren.

## 3. Tageskontingent

### Bestehende Semantik

Ein durch den Parallelitäts-Lock abgewiesener Start verbraucht bereits heute kein Kontingent.
Die Quoten werden erst reserviert, nachdem kein anderer aktiver Run mehr blockiert.

Ein tatsächlich zugelassener Provider-Aufruf zählt dagegen auch dann als Aufruf, wenn seine
Antwort abgeschnitten wird, einen Providerfehler liefert oder später die fachliche
Vertragsvalidierung nicht besteht. Das bleibt bewusst so, weil diese Aufrufe reale
Providerkapazität beziehungsweise Kosten verbrauchen und die Quote genau diesen Verbrauch
begrenzen soll.

### Korrektur für den Testbetrieb

Das bisherige Prozesslimit von drei Aufrufen pro Tag ist für die manuelle Erprobung zu eng.
Block 7 erhält deshalb ein eigenes Prozesslimit
`ACCELERATOR_SOLUTION_GENERATION_MAX_CALLS_PER_CONTEXT` mit Default 10. Benutzer- und globale
Tagesgrenzen bleiben unverändert bei standardmäßig 20 beziehungsweise 100 Aufrufen. Bereits
vorhandene Quotenstände werden weiterverwendet; es ist kein Datenreset nötig.

## 4. „Mindestens zwei unterschiedliche Lösungsoptionen“

### Ursache

Dieser Text stammt nicht aus dem Block-7-Generierungsvertrag. Er wird von
`ki_radar.architecture.solution_selection.comparison_blockers()` erzeugt, wenn für die
bestehende Auswahlmatrix weniger als zwei persistierte `SolutionOption`-Objekte vorhanden sind.
Er verhindert eine fachliche Auswahlentscheidung mit nur einer Alternative.

Die Block-7-Validierung vergleicht ausschließlich die drei neu generierten Lanes untereinander.
Bereits vorhandene manuelle Optionen werden dort nicht gelesen und können ein gültiges
Dreier-Bundle nicht ungültig machen.

Die beobachtete Kombination aus generischem KI-Sicherheitsfehler und dem Vergleichsblocker war
daher irreführend: Der Vergleichsblocker erklärte nur den Zustand der bereits gespeicherten
Optionen, nicht die Ursache der verworfenen KI-Antwort.

### Korrektur

Bei `invalid_generation_payload` wird nun zusätzlich ein begrenzter, serverseitig erzeugter
`Validierungsgrund` aus maximal drei Contract-Fehlern angezeigt. Dadurch bleibt die
Fail-closed-Regel bestehen, während der tatsächliche Grund der KI-Verwerfung sichtbar und klar
vom bestehenden Auswahlblocker getrennt wird.

## Regression

Der Nachtrag ergänzt beziehungsweise verschärft Tests für:

- das dedizierte 8192-Token-Budget des Block-7-Bundles,
- Freigabe des Locks nach `output_truncated`,
- Recovery eines verwaisten `RUNNING`-Runs,
- keine zusätzliche Quotenzählung bei einem serverseitig blockierten Parallelstart,
- das dedizierte Prozesskontingent für Block 7,
- erfolgreiche Generierung trotz bereits vorhandener manueller Lösungsoption,
- sichtbaren Contract-Validierungsgrund,
- klare Herkunft des „Mindestens zwei …“-Hinweises aus der bestehenden Auswahlmatrix.

Die fachliche Blockgrenze bleibt unverändert: keine automatische Bewertung, Präferenz,
Auswahlentscheidung, Governance-, Delivery- oder Lifecycle-Änderung.
