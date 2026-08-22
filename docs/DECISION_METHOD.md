# Entscheidungsmethodik für KI-Use-Cases

## Ziel

KI-Radar trennt mehrere fachlich unterschiedliche Entscheidungen bewusst voneinander:

1. **Discovery-Lösungsentscheidung:** Welche Intervention ist für das analysierte Problem die beste ausreichende Lösung – organisatorisch, klassische Automation, KI oder Hybrid?
2. **Use-Case-Bewertung:** Ist ein tatsächlich angelegter KI-Use-Case fachlich und technisch ausreichend belastbar bewertet?
3. **Verbindliche Freigabe:** Darf der bewertete Use Case unter den geltenden Governance- und Rollenregeln weitergeführt werden?

Eine positive Freigabe ist nur möglich, wenn die Aufnahme vollständig, die Bewertung evidenzbasiert und die Rollentrennung eingehalten ist. Eine vorgelagerte Discovery-Entscheidung erzeugt dagegen **nicht automatisch** einen KI-Use-Case.

## Vorgelagerte Lösungsentscheidung in Discovery

Vor der Use-Case-Aufnahme kann eine Prozessanalyse mehrere Lösungsoptionen vergleichen. Dabei gelten seit #331 folgende Invarianten:

- organisatorische beziehungsweise standardisierende Lösungen, klassische Automation, KI und hybride Lösungen sind gleichwertig zulässige Lösungsklassen;
- Time-to-Value ist ein sichtbarer qualitativer Trade-off, **kein automatischer Dominanzscore**;
- die Auswahlbegründung muss Problem-Fit, erwarteten Nutzen, Machbarkeit, Datenanforderungen, Integrationsaufwand, Risiken, Architecture Fit und Time-to-Value nachvollziehbar abwägen;
- eine Option kann auf einer **Hypothese**, einem **Indiz** oder einem **Messwert/Nachweis** beruhen; eine fachliche Prozessvalidierung bleibt davon als eigener Validierungsnachweis getrennt;
- eine frühe Hypothese ist zulässig, darf in der UI und im Entscheidungssnapshot aber nicht wie validierte Evidenz erscheinen;
- die Auswahl wird als unveränderlicher Entscheidungsstand mit Vergleichs-, Diagnose- und Evidenzkontext historisiert;
- ein bevorzugter Non-AI-Ansatz ist ein gültiger Abschluss der Discovery und erzeugt keine verpflichtende Next Action `KI-Use-Case anlegen`;
- bei Hybrid-, Custom- oder sonstigen Optionen wird ein KI-Anteil explizit behandelt und nicht automatisch aus dem Lösungstyp abgeleitet;
- LLM-Funktionen dürfen Optionen entwerfen, aber keine bindende Präferenz, No-AI-Entscheidung oder Use-Case-Anlage auslösen.

Damit gilt fachlich:

```text
Problem / Ursache / Potenzial
→ technologieoffener Lösungsraum
→ begründete bevorzugte Lösung
→ nur bei tatsächlicher KI-Komponente ggf. KI-Use-Case
```

Die folgenden Abschnitte beschreiben die **nachgelagerte Use-Case-Bewertung und Freigabe**, sobald ein Use Case tatsächlich existiert.

## Entscheidungsstatus

- **In Klärung:** Pflichtangaben für eine Bewertung fehlen.
- **Bereit zur Bewertung:** Die geführte Aufnahme ist vollständig.
- **Zurückgestellt:** Behebbare Voraussetzungen oder Evidenzen fehlen.
- **Freigegeben:** Alle Muss-Anforderungen sind erfüllt und eine von der Bewertung getrennte Person hat entschieden.
- **Freigegeben mit Auflagen:** Alle Muss-Anforderungen sind erfüllt, Auflage, Verantwortung und Frist sind dokumentiert und eine zweite unabhängige berechtigte Person hat bestätigt.
- **Nicht weiterverfolgt:** Ein begründeter Ausschluss- oder Abbruchgrund liegt vor.

## Rollen

### Fachlich verantwortliche Person

Erfasst Problem, Prozess, Nutzenhypothese und Datenrahmen. Sie kann keine verbindliche Freigabe für den eigenen Use Case erteilen oder als zweite freigebende Person auftreten.

### Bewertende Person

Bewertet wirtschaftlichen Nutzen, strategischen Beitrag, technische Machbarkeit, Datenreife sowie Risiko und Komplexität. Sie dokumentiert Evidenz, Annahmen und Empfehlung, entscheidet aber nicht über die eigene Bewertung.

### Entscheidungsverantwortliche Person

Prüft Bewertung, hergeleitete Confidence, Governance-Vorprüfung und Pflichtprüfungen. Sie muss von der bewertenden und der fachlich verantwortlichen Person verschieden sein.

### Governance-Fallback

Existiert keine dedizierte Governance-prüfende Person, führt die bewertende Person die operative Vorprüfung durch. Die entscheidungsverantwortliche Person muss diese separat bestätigen. Eine positive Entscheidung bleibt blockiert, solange diese Bestätigung oder eine erforderliche Datenschutz-, Informationssicherheits- oder Rechtsprüfung fehlt.

## Confidence-Herleitung

Confidence ist keine freie Selbsteinschätzung. Sie wird aus fünf Faktoren abgeleitet:

1. Qualität der Evidenz
2. Aktualität
3. Abdeckung
4. unabhängige Prüfung
5. Klärung offener Annahmen

**Hoch:** mindestens repräsentative Evidenz und alle übrigen Faktoren mindestens belastbar.  
**Mittel:** mindestens fachliche Einschätzung und alle übrigen Faktoren mindestens eingeschränkt.  
**Niedrig:** mindestens eine dieser Mindestbedingungen ist nicht erfüllt.

Eine niedrige Confidence blockiert `Freigegeben` und `Freigegeben mit Auflagen`. Sie verändert keinen künstlichen Gesamtscore.

## Verbindliche Sperren

Eine positive Entscheidung ist serverseitig ausgeschlossen, wenn mindestens einer der folgenden Punkte zutrifft:

- Pflichtangaben aus der geführten Aufnahme fehlen
- keine aktuelle strukturierte Bewertung existiert
- bewertende und entscheidende Person sind identisch
- fachlich verantwortliche und entscheidende Person sind identisch
- Confidence ist niedrig
- technische Machbarkeit oder Datenreife ist niedrig
- Risiko und Komplexität ist hoch
- Governance-Vorprüfung wurde nicht durchgeführt oder separat bestätigt
- eine als erforderlich markierte Datenschutz-, Informationssicherheits- oder Rechtsprüfung ist offen

Für `Freigegeben mit Auflagen` gelten zusätzlich:

- Auflage, verantwortliche Person und Fälligkeit sind Pflicht
- die erste Entscheidung verändert den Use-Case-Status noch nicht
- eine zweite berechtigte Person muss bestätigen
- die zweite Person muss von bewertender, fachlich verantwortlicher und zuerst entscheidender Person verschieden sein

## Kopplung an den Lifecycle

Der Wechsel in `Pilot` oder `Betrieb` ist nur möglich, wenn der Entscheidungsstatus `Freigegeben` oder `Freigegeben mit Auflagen` lautet. Die bestehende Lifecycle-Prüfung bleibt zusätzlich aktiv; eine Freigabe ersetzt daher weder Governance-Screening noch Metrik-, Betriebs- oder Go-live-Anforderungen.

## Versionierung

Jede Bewertung erhält eine fortlaufende Version. Entscheidungen referenzieren die konkrete Bewertungsversion. Historische Bewertungen und Entscheidungen werden nicht überschrieben.

Auch die vorgelagerte Discovery-Lösungspräferenz besitzt eine eigene immutable Entscheidungshistorie. Eine spätere Neubewertung erzeugt einen neuen Entscheidungsstand und löscht oder verändert bestehende Downstream-Artefakte nicht automatisch.

## Abgrenzung PR A

PR A enthält keine Nutzenkalibrierung, Portfolio-Aggregation, Strategieauswertung oder Delivery-Handover-Logik. Diese Funktionen bleiben getrennten Produktinkrementen vorbehalten.
