# Validierungsplan für den externen Produktpfad

**Version:** 1.0  
**Status:** Entscheidungs- und Arbeitsplan

## 1. Ziel und Ausgangslage

Dieser Plan hält die unternehmerische Entscheidung fest, ob KI-Radar als externe KMU-Lösung, Consulting Accelerator oder übertragbares Asset für eine neue Rolle weiterentwickelt werden soll. Er ergänzt den technischen und methodischen [Plan für Baseline-Abschluss und KI-beschleunigte Delivery](AI_ACCELERATION_PLAN.md), ersetzt ihn aber nicht.

Der Referenzdurchlauf `KI-0154` belegt, dass der vollständige Weg vom Value Stream bis zum Pilotstart grundsätzlich funktioniert. Er belegt noch nicht, dass externe Organisationen diesen Prozess in dieser Tiefe benötigen, ihre bestehenden Werkzeuge als unzureichend ansehen oder dafür Budget und Einführungskapazität bereitstellen.

Vor weiterem Copilot-Ausbau müssen daher folgende Fragen mit externer Evidenz beantwortet werden:

- Tritt das angenommene Problem wiederkehrend auf?
- Verursacht es relevante Nacharbeit, Verzögerung, Kosten, Risiken oder Qualitätsverlust?
- Wo reichen Excel, Jira, Confluence und bestehende Meetings aus, und wo nicht?
- Wer trägt das Problem, wer nutzt den Prozess und wer kann Budget freigeben?
- Gibt es konkrete Folgehandlungen oder nur unverbindliche Zustimmung?

Unabhängig vom Ergebnis bleibt das Repository als Wissenssystem, Interview- und Karriere-Asset sowie methodische Referenz nutzbar. Continue/Pivot/Stop betrifft den zusätzlichen externen Produktpfad.

---

## 2. Zwei parallele Arbeitsstränge

### Strang A: Technische Baseline

- offene P0- und P1-A-Fehler beheben,
- Golden Path ohne Datenbankeingriff, manuelle URL-Aufrufe oder Rollen-Workarounds erneut durchführen,
- reproduzierbaren Stand als manuelle Baseline taggen.

### Strang B: Marktvalidierung

- fünf bis acht reale Problemgespräche führen,
- vergangene konkrete Abläufe statt Meinungen zu einer Produktidee untersuchen,
- Problemhäufigkeit, Auswirkungen, Alternativen, Budget und Kaufprozess erfassen,
- anschließend Continue, Pivot oder Stop entscheiden.

### Vorrangregel

Bei Zeit- oder Ressourcenkonflikten hat **Strang B Vorrang**, weil er die größere Unsicherheit klärt und von der Verfügbarkeit externer Gesprächspartner abhängt.

1. Vereinbarte Interviews sowie deren Vor- und Nachbereitung werden nicht für technische Detailarbeit verschoben.
2. Strang A wird in den verbleibenden Zeitfenstern fortgeführt.
3. Neue P1-B-, P2- oder allgemeine Governance-Vertiefungen beginnen erst nach der Validierungsentscheidung.
4. Kritische P0-Korrekturen dürfen vorgezogen werden, wenn sie Datenintegrität oder einen vereinbarten Validierungstermin gefährden.

---

## 3. Interviewumfang und Dokumentation

### Mindestumfang

- fünf bis acht Gespräche,
- nach Möglichkeit mehrere Organisationen,
- alle drei Perspektiven aus Abschnitt 5,
- mindestens zwei Gespräche mit Economic Buyern oder Personen mit nachweislich maßgeblichem Budgeteinfluss.

### Pro Gespräch dokumentieren

- Rolle, Organisationstyp und Perspektive,
- zuletzt geschilderter konkreter Fall,
- beteiligte Personen, Werkzeuge und Artefakte,
- Rückfragen, Medienbrüche und erneute Arbeiten,
- Zeit-, Kosten-, Risiko- oder Qualitätsauswirkung,
- Häufigkeit des Problems,
- bestehender Workaround und Zufriedenheit damit,
- Budgetzuständigkeit und Beschaffungsweg,
- geäußertes Interesse,
- tatsächlich vereinbarte Folgehandlung,
- Gegenbelege und Gründe für fehlenden Bedarf.

Mündliches Interesse und konkrete Folgehandlungen werden getrennt erfasst.

---

## 4. Interviewleitfaden

### Grundregel

Das Gespräch beginnt nicht mit Produktpräsentation, Repository, CRISP-ML(Q) oder gewünschter Lösung. Zuerst wird ein realer vergangener Vorgang rekonstruiert.

### Einstiegsfrage

> Erzählen Sie mir vom letzten KI-Use-Case, der vom Fachbereich an ein Umsetzungs- oder Pilotteam übergeben wurde. Was ist danach konkret passiert?

Falls kein solcher Fall bekannt ist:

> Erzählen Sie mir vom letzten KI-Vorhaben, bei dem entschieden werden musste, ob es vertieft, pilotiert oder umgesetzt wird. Wie lief diese Entscheidung konkret ab?

### Vertiefende Nachfragen

**Ablauf und Verantwortung**

- Wer initiierte das Vorhaben, lieferte Informationen, entschied und übernahm die Umsetzung?
- Wo wechselte die Verantwortung zwischen Personen oder Teams?

**Artefakte und Systeme**

- Welche Tabellen, Dokumente, Tickets oder Präsentationen wurden verwendet?
- Wo lagen Scope, Nutzen, Datenquellen, Risiken und Verantwortlichkeiten?
- Welche Informationen mussten erneut übertragen oder erklärt werden?
- Welches System galt bei Widersprüchen als führend?

**Reibung und Auswirkung**

- Welche Rückfragen kamen nach der Übergabe erneut auf?
- Was fehlte oder war widersprüchlich?
- Wer arbeitete nach und wie lange dauerte die Klärung?
- Welche Termine, Kosten, Risiken oder Qualitätsprobleme entstanden?
- Wie häufig tritt das Muster auf und was passiert ohne Verbesserung?

**Bestehende Alternativen**

- Was funktioniert mit Excel, Jira, Confluence oder bestehenden Meetings gut?
- Wo reichen diese Lösungen konkret nicht aus?
- Welche Verbesserungen wurden bereits versucht und warum blieb das Problem bestehen?

**Budget und Einführung**

- Wer besitzt das Problem organisatorisch?
- Wer könnte eine Änderung beauftragen und aus welchem Budget?
- Wer müsste einem Test zustimmen?
- Welche Bedingungen müssten für einen kleinen Test erfüllt sein?

Erst danach darf ein kurzer Konzeptausschnitt gezeigt werden. Anschließend wird konkret gefragt, welcher Teil den beschriebenen Ablauf verändern würde, was unnötig wäre, welche Alternative einfacher bleibt und wer der nächste notwendige Gesprächspartner ist.

Folgende Aussagen gelten allein nicht als belastbare Evidenz:

- „Klingt interessant.“
- „Das könnten wir uns vorstellen.“
- „So etwas wäre grundsätzlich hilfreich.“
- „Melden Sie sich, wenn es fertig ist.“

---

## 5. Zielgruppen-Matrix

| Perspektive | Typische Rollen | Erkenntnisziel | Mindestabdeckung |
|---|---|---|---:|
| **Problemträger** | Head of Data & AI, AI Lead, Governance Lead, Portfolio- oder Innovationsmanager | Häufigkeit, Schmerz, Risiken, organisatorische Verantwortung | mindestens 2 Gespräche |
| **Prozessnutzer** | Business Owner, Technical Owner, Delivery Lead, Product Owner, Solution Architect | realer Ablauf, Medienbrüche, Wiederholungen, Bedienaufwand | mindestens 2 Gespräche |
| **Economic Buyer** | CIO, CTO, Bereichsleitung, Transformation Lead, budgetverantwortliche Programmleitung | Budgetrelevanz, Kaufprozess, Alternativen, Pilotbereitschaft | mindestens 2 Gespräche |

Eine Person kann mehrere Perspektiven abdecken, wenn die jeweilige Verantwortung konkret belegt ist. Positive Signale ausschließlich von Problemträgern ohne Budget- oder Einführungsbezug reichen nicht für Continue.

---

## 6. Harte und weiche Signale

### Weiche Signale

Mündliches Interesse, Zustimmung zur Problembeschreibung, positive Demo-Reaktion oder Bitte um spätere Informationen. Diese Signale werden dokumentiert, reichen aber nicht für Continue.

### Harte Signale

Mindestens eine konkrete Folgehandlung, beispielsweise:

- terminierter Folgetermin zu einem konkreten Anwendungsfall,
- tatsächlich erfolgte Einführung zu einem weiteren Stakeholder oder Economic Buyer,
- bereitgestelltes anonymisiertes oder synthetisches reales Artefakt,
- klar abgegrenzter Pilot- oder Konzepttest mit benannten Beteiligten,
- schriftlich bestätigte interne Prüfung mit Datum und Verantwortlichkeit,
- Einladung zur Prüfung in einem realen Portfolio-, Governance- oder Delivery-Kontext.

Eine mündliche Zusage zählt erst, wenn der nächste Schritt terminiert, die Einführung erfolgt oder das vereinbarte Artefakt bereitgestellt wurde.

---

## 7. Scope und Timebox des ersten Copilot-Prototyps

### Zielhypothese

> Kann ein Modell aus vorhandener bestätigter Evidenz nachvollziehbare und brauchbare Vorschläge für ausgewählte Delivery-Package-Felder erzeugen, ohne Quellen zu erfinden oder menschliche Bestätigung zu ersetzen?

### Timebox

- maximal fünf Arbeitstage aktive Entwicklungszeit,
- Start- und Endtermin vor Beginn festlegen,
- keine automatische Verlängerung,
- neue Anforderungen ausschließlich in ein separates Backlog aufnehmen.

### Enthaltener Scope

- nur vorhandene interne Artefakte als Quellen,
- höchstens ein bis zwei Delivery-Sektionen,
- strukturierte Feldvorschläge mit sichtbarem Quellenbezug,
- Kennzeichnung von Lücken, Annahmen und Konflikten,
- manuelle Übernahme, Änderung oder Verwerfung,
- bestehende Herkunfts- und Reviewlogik nutzen.

### Ausgeschlossen

- alle sieben Delivery-Sektionen,
- Datei- und Office-Extraktion,
- Connectoren,
- freie Chatoberfläche,
- automatische Use-Case-Erstellung,
- neue allgemeine Governance- oder Rollenmodelle,
- automatische Bestätigung oder Freigabe,
- Produktionshärtung, Skalierung oder Multi-Tenancy,
- nicht unmittelbar prototyprelevante P1-B- oder P2-Optimierungen.

Am Ende der Timebox wird bewertet, ob die Vorschläge fachlich verwertbar und quellengebunden sind, Lücken statt Tatsachen erfinden, einen erkennbaren Zeitvorteil erzeugen und gemeinsam mit der Marktvalidierung weiteren Ausbau rechtfertigen.

---

## 8. Continue/Pivot/Stop

Die Kriterien werden vor den Gesprächen festgelegt und nicht nachträglich an gewünschte Ergebnisse angepasst.

### Continue

Alle folgenden Bedingungen müssen erfüllt sein:

1. Mindestens drei Gesprächspartner aus mindestens zwei Organisationen schildern unabhängig ein vergleichbares, wiederkehrendes Problem anhand vergangener Fälle.
2. Mindestens zwei benennen oder quantifizieren relevante Nacharbeit, Verzögerung, Kosten, Risiken oder Qualitätsverlust.
3. Mindestens zwei bewerten den bestehenden Workaround an einer konkreten Stelle als unzureichend.
4. Mindestens zwei Economic Buyer oder maßgeblich Budgetbeeinflussende bestätigen Budget- oder Priorisierungsrelevanz.
5. Mindestens eine Organisation setzt ein hartes Signal aus Abschnitt 6 tatsächlich um.
6. Es liegt kein dominanter Gegenbeleg vor, dass passende Organisationen das Problem mit vorhandenen Werkzeugen ausreichend und wirtschaftlich lösen.

Unverbindliche Zustimmung erfüllt Bedingung 5 nicht.

### Pivot

Pivot erfolgt, wenn ein relevantes Problem belegt ist, aber beispielsweise:

- der größte Schmerz in Discovery, Priorisierung, Evidenzsammlung oder Reporting statt im Delivery-Handover liegt,
- ein Beratungs- oder Enablement-Service stärker nachgefragt wird als ein Self-Service-Produkt,
- der Nutzen primär als internes Asset für AI Leads, Berater oder Solution Architects entsteht,
- bestehende Werkzeuge führend bleiben, aber ein enger Prüf- oder Beschleunigungsbaustein Wert besitzt,
- die wirtschaftlich relevante Zielgruppe enger oder anders als „KMU“ ist.

Für den Pivot werden Problem, Zielgruppe, Wertversprechen und nächster Test ausdrücklich neu formuliert.

### Stop

Der externe Produktpfad wird vorerst gestoppt, wenn keine Continue-Bedingung erreicht wird und mehrere Befunde zusammen auftreten:

- weniger als drei Personen beschreiben ein vergleichbares wiederkehrendes Problem,
- bestehende Werkzeuge und Meetings reichen überwiegend aus,
- Auswirkungen lassen sich nicht konkret belegen,
- Economic Buyer sehen keine Budget- oder Priorisierungsrelevanz,
- keine Organisation setzt ein hartes Signal um,
- Interesse entsteht nur nach ausführlicher Framework- oder Tool-Erklärung,
- der Copilot würde vor allem einen Prozess beschleunigen, den die Zielgruppe nicht durchführen will.

Stop bedeutet keinen Ausbau von Uploads, Connectoren oder breiter Copilot-Funktionalität auf Basis der aktuellen Hypothese. Das Repository bleibt als Wissens-, Karriere- und Consulting-Asset erhalten.

---

## 9. Entscheidungsprotokoll

Nach Abschluss werden mindestens dokumentiert:

- Anzahl, Organisationen und Zusammensetzung der Gespräche,
- Abdeckung der drei Perspektiven,
- wiederkehrende Problemmuster und konkrete Auswirkungen,
- bestehende Alternativen,
- Anzahl und Art harter Folgehandlungen,
- Gegenbelege,
- Entscheidung Continue, Pivot oder Stop,
- Begründung anhand der vorab festgelegten Kriterien,
- nächster begrenzter Schritt und ausdrücklich verworfene Folgearbeiten.

Die Entscheidung basiert nicht auf Begeisterung für das Konzept, vorhandener Featurezahl oder bereits investierter Entwicklungszeit.
