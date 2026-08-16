# Value-Stream-Methodik

**Version:** 1.0  
**Gültig für:** Value-Stream-Erfassung und Fokus-/Prozessanalyse im KI-Radar  
**Zweck:** kompakte fachliche Leitplanke; keine zusätzliche Business-Architecture-Schicht

## 1. Begriffe sauber trennen

### Capability

Eine Capability beschreibt, **was ein Unternehmen können muss**. Sie ist eine relativ stabile Fähigkeit und noch kein konkreter Ablauf.

Beispiel: `Rechnungen prüfen und freigeben können`.

### Value Stream

Ein Value Stream beschreibt, **wie für einen Stakeholder ein relevantes Ergebnis oder ein Wert entsteht**. Er verbindet einen klaren Trigger mit einem fachlich relevanten Outcome.

Beispiel: `Rechnungseingang bis freigegebene Zahlung`.

### Process

Ein Process beschreibt, **wie ein konkreter Ablauf heute oder künftig ausgeführt wird**: Schritte, Rollen, Systeme, Regeln, Übergaben und Ausnahmen.

Beispiel: der operative Prüf- und Freigabeprozess innerhalb einer ausgewählten Value-Stream-Phase.

> Merksatz: **Capability = Was können? · Value Stream = Wie entsteht Wert? · Process = Wie läuft es konkret ab?**

## 2. Einen Value Stream sinnvoll schneiden

Ein guter Value Stream besitzt einen erkennbaren Anfang und ein fachlich relevantes Ende.

- **Trigger:** Welches Ereignis startet die Wertentstehung?
- **Stakeholder / Empfänger:** Für wen entsteht das relevante Ergebnis?
- **Outcome:** Welcher Zustand oder welches Ergebnis liegt am Ende vor?
- **Scope-In:** Was gehört ausdrücklich zum betrachteten Value Stream?
- **Scope-Out:** Was gehört ausdrücklich nicht dazu?
- **Strategischer Kontext / Ziel:** Warum ist dieser Value Stream für das Unternehmen relevant?

### Kurzbeispiel

**Value Stream:** Beschaffungsbedarf bis Bestellung  
**Trigger:** Ein bestätigter Beschaffungsbedarf liegt vor.  
**Stakeholder:** Bedarfsträger und Einkauf.  
**Outcome:** Eine fachlich und kaufmännisch freigegebene Bestellung wurde ausgelöst.  
**Scope-In:** Bedarf konkretisieren, Anbieter/Angebote prüfen, Entscheidung und Bestellung.  
**Scope-Out:** Wareneingang, Rechnungsprüfung und Zahlung.

## 3. Granularität konsistent halten

Value Streams, die miteinander verglichen werden, sollten auf einer ähnlichen Abstraktionsebene liegen.

Vermeiden:

- einen End-to-End-Value-Stream mit einem einzelnen Teilprozess zu vergleichen,
- einzelne Tätigkeiten als eigene Value Streams zu behandeln,
- organisatorische Zuständigkeiten mit Wertentstehung gleichzusetzen.

Prüffrage:

> Beschreiben die betrachteten Value Streams jeweils einen vergleichbaren Weg von einem Trigger zu einem für einen Stakeholder relevanten Outcome?

## 4. Phasen als Wertfortschritt beschreiben

Eine Value-Stream-Phase ist mehr als eine Tätigkeitsüberschrift. Sie sollte einen **erkennbaren fachlichen Wertfortschritt** beschreiben.

Für jede Phase helfen drei Fragen:

1. **Was liegt vorher vor?**
2. **Was verändert sich fachlich?**
3. **Welcher relevante Zustand oder welches Ergebnis liegt danach vor?**

Als Denkmodell kann verwendet werden:

`Entrance → Transformation → Value Item / Wertfortschritt → Exit`

Dieses Denkmodell dient nur zum besseren Schneiden und Beschreiben der Phase. Es wird **nicht** in vier zusätzliche Pflichtfelder übersetzt.

### Beispiel

Schwach: `Angebote bearbeiten`

Stärker: `Angebote vergleichbar machen` – aus eingegangenen, unterschiedlich strukturierten Angeboten entsteht eine fachlich vergleichbare Entscheidungsgrundlage.

## 5. Mehrere mögliche Value Streams pragmatisch priorisieren

Wenn mehrere Value Streams als Startpunkt infrage kommen, kann eine einfache Heuristik verwendet werden:

`Business Importance × Transformation Need`

### Business Importance

Wie wichtig ist der Value Stream für das Unternehmen oder relevante Stakeholder?

Mögliche Indikatoren:

- Einfluss auf strategische Ziele,
- Kunden-/Stakeholder-Wert,
- wirtschaftliche Relevanz,
- regulatorische oder operative Kritikalität.

### Transformation Need

Wie groß ist der konkrete Veränderungsbedarf?

Mögliche Indikatoren:

- bekannte Probleme und Engpässe,
- hohe manuelle Aufwände,
- Medienbrüche,
- Qualitätsprobleme,
- hoher Änderungsdruck,
- relevantes Automatisierungs- oder Digitalisierungspotenzial.

### Einfache Orientierung

| Business Importance | Transformation Need | Orientierung |
|---|---|---|
| hoch | hoch | bevorzugt vertiefen |
| hoch | niedrig | beobachten / gezielt prüfen |
| niedrig | hoch | Nutzen und Scope kritisch prüfen |
| niedrig | niedrig | nachrangig |

Diese Heuristik ist **kein neues Portfolio-Modul und kein verpflichtendes Scoring**. Sie hilft lediglich, einen sinnvollen Startpunkt zu wählen.

## 6. Von Value Stream zu Prozess und Lösung

Der KI-Radar folgt bewusst dieser Logik:

1. Value Stream erfassen und sauber abgrenzen.
2. Phasen vergleichen.
3. Fokusphase nachvollziehbar auswählen.
4. Den relevanten Prozess detaillierter analysieren.
5. Ursachen, Engpässe, Baselines und Rahmenbedingungen verstehen.
6. Mehrere Lösungsoptionen entwickeln und vergleichen.
7. Die fachlich beste Option auswählen.

Dabei gilt:

> **Problem / Prozess → Lösungsraum → mehrere Alternativen → KI kann eine Option sein.**

Nicht:

> **Problem → KI-Eignung → KI erzwingen.**

Organisatorische, regelbasierte oder klassische technische Lösungen können gegenüber einer KI-Lösung die bessere Option sein.

## 7. Bestehende qualitative Bewertungsskalen

Die bestehende Value-Stream-/Fokus-Journey verwendet die drei Stufen:

`Niedrig · Mittel · Hoch`

Die konkrete Bedeutung hängt vom Kriterium ab. Deshalb gilt nicht pauschal „hoch = gut“.

- **Strategischer Impact / Impact:** Reichweite und Relevanz der Wirkung.
- **Wirtschaftliches Potenzial:** Größe des plausiblen wirtschaftlichen Hebels.
- **Problemintensität:** Stärke, Häufigkeit und Konsequenz des Problems.
- **Datenzugänglichkeit / Datenlage:** reale Verfügbarkeit, Zugänglichkeit und Nutzbarkeit relevanter Daten.
- **Veränderungsaufwand:** notwendiger organisatorischer, prozessualer und technischer Veränderungsaufwand.

Die Skalenanker in der Anwendung erläutern diese bestehende Semantik; sie verändern die Bewertungslogik nicht.

## 8. Methodische Leitplanke

Die Value-Stream-Erfassung soll Orientierung schaffen, nicht zusätzliche Bürokratie erzeugen.

Daher:

- vorhandene Felder zuerst nutzen,
- keine zusätzliche Capability- oder Portfolio-Engine,
- keine neuen Pflichtfelder nur für Methodik,
- keine parallele Fokus- oder Prozessanalyse,
- kein vorgeschaltetes AI-Suitability-Gate,
- Detailtiefe erst dort erhöhen, wo eine Fokusentscheidung dies rechtfertigt.
