# Block 9 AP 7 Nachtrag: Eingefrorener Benchmarkvertrag `block9-v2`

**Issue:** #125  
**Fixture:** `ki_radar/accelerator/block9_benchmark.v2.json`  
**Kanonische SHA-256-Prüfsumme:** `d4f7431ac68bb94b05885ae25f323e4147cf68fb20977ecd18c2acdeef74e6d1`  
**Ersetzt für interaktive AP-9-Läufe:** `block9-v1`

## 1. Messgrenze

Gemessen wird die menschliche Bedienzeit vom ersten gewerteten UI-Schritt bis zum
vollständigen **fachlichen Erfassungsstand** der 21 eingefrorenen Scoring-Felder.

`status=idea` bleibt erhalten. `decision_status` ist kein Scoring-Feld und wird nicht
künstlich zwischen Pfaden normalisiert. Fachliche Gates, Freigaben, Delivery-Handover,
Pilotstart und Go-live bleiben außerhalb des Primärbenchmarks.

## 2. Manual-Pfad

Start ist weiterhin der reguläre Sechs-Schritt-Intake.

Der reale Intake enthält nicht alle 21 Scoring-Felder. Nach dem normalen Step-6-Submit wird
deshalb der reguläre Use-Case-Edit genutzt, um ausschließlich die eingefrorenen Fakten für
folgende Scoring-Felder zu vervollständigen:

- `interface_description`
- `benefit_category`
- `human_oversight`

Diese Navigation, Eingabe, Prüfung und Korrektur zählt vollständig zur gemessenen Zeit.

Der Intake setzt produktseitig `decision_status=ready`. Dieser Wert wird nur protokolliert,
nicht als Beschleunigungs- oder Qualitätsmetrik bewertet.

## 3. Accelerator-Pfad

Vor dem Start der Messuhr existieren technisch unvermeidbar:

- eine neue CaptureSession,
- ein minimales bearbeitbares Benchmark-UseCase-Ziel,
- die bestehende One-Target-Bindung.

Die Uhr startet mit der ersten Nutzeraktion in Schritt 1 der vorbereiteten CaptureSession.

Danach gehören zur gemessenen Strecke:

1. geführte Capture-Eingabe,
2. Review und Abschluss,
3. LLM-Analyse einschließlich Wartezeit,
4. Candidate-Review,
5. direkte beziehungsweise bearbeitete Adoption oder Verwerfen,
6. Structured Review für unterstützte strukturierte Metriken,
7. regulärer Use-Case-Edit für verbleibende Scoring-Felder, die nicht über Adoption
   geschrieben werden können,
8. finaler Save/Review.

Es gibt keinen Zeitabzug für den Wechsel zwischen diesen vorhandenen Oberflächen.

## 4. Zusätzliche eingefrorene Pfadfakten

Damit der reale Manual-Pfad ohne Erfindungen ausgeführt werden kann, gelten für A und B
zusätzlich:

- Business Unit: `[BENCHMARK] Prozesse & Organisation`
- Business Owner: `benchmark_business_owner`
- Submitter/Operator: `benchmark_operator`
- Fachdomäne: `procurement` / Einkauf und Beschaffung
- Business Capability: `Source-to-Pay`
- Hosting: `unknown` / Noch offen
- Governance-Checkboxen im Manual-Intake: `false`
- Produktname: unbekannt
- Priorität: nicht als fachlicher Benchmarkfakt vorgegeben

Diese Angaben sind keine zusätzlichen Scoring-Felder.

## 5. Benchmark A

A bleibt der Golden Path. Alle 21 Scoring-Felder besitzen einen eindeutigen fachlichen Wert.
Provider, Modell und Support-Verantwortung bleiben ausdrücklich unbekannt und dürfen nicht
erfunden werden.

Die Summary ist in v2 auf die reale Intake-Semantik **„Heutiger Ablauf und Auslöser“**
zugeschnitten. `source_systems` und `data_sources` bleiben getrennte Fakten.

## 6. Benchmark B

B ist ein Accelerator-Robustheitslauf mit Run-ID:

`accelerator-B-1`

Er enthält bei ansonsten vollständiger fachlicher Scoring-Grundlage genau:

- eine fehlende Support-Verantwortung,
- einen Quellenkonflikt beim Zielwert `8.25` versus `8.5`,
- eine Scope-Falle rund um finale Lieferantenauswahl und Vergabeentscheidung,
- Baseline `11 Minuten`,
- unbekannten Provider und unbekanntes Modell.

Erwartung:

- Support bleibt offen.
- Kein Zielwert wird still bevorzugt.
- Finale Lieferantenauswahl/Vergabeentscheidung werden nicht als erlaubter Zweck behandelt.
- Baseline und Einheit werden korrekt normalisiert.
- Provider, Modell und Support werden nicht erfunden.

## 7. Reihenfolge

Vor den Scored Runs erfolgt ein nicht gewerteter Warm-up zur Pfadvalidierung.

Danach unverändert:

1. `manual-A-1`
2. `accelerator-A-1`
3. `accelerator-A-2`
4. `manual-A-2`
5. `manual-A-3`
6. `accelerator-A-3`

Danach:

7. `accelerator-B-1`

Wenn der Warm-up einen eingefrorenen Pfad erneut als technisch nicht erreichbar zeigt,
dürfen keine Scored Runs starten.

## 8. Technische AP-9-Werte

Der Blueprint-Kontrolllauf und die drei Delivery-Mapping-Läufe aus dem bisherigen AP 9
werden nicht erneut gemessen. Der Nachtrag verändert weder deren Eingaben noch Prüfsummen,
Mappinglogik oder Messgrenze.

Sie bleiben als technische Rohdaten erhalten. Die interaktiven menschlichen Läufe werden
dagegen ausdrücklich mit `benchmark_version=block9-v2` aufgezeichnet.

## 9. Raw-Regel

Jeder gestartete Scored Run wird unverändert protokolliert, auch wenn er fehlschlägt,
abgebrochen wird oder ein ungünstiges Ergebnis liefert.

Keine Aussage zu „unter 30 Minuten“ und kein Beschleunigungsfaktor vor AP 10.
