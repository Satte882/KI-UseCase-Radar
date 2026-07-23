# KI-Radar Design System

Dieses Dokument ist die verbindliche UI-Zwangsjacke für neue oder geänderte Oberflächen.
Es beschreibt Produktqualität, nicht eine austauschbare Landingpage-Ästhetik.

## Zielbild

- Ruhige, hochwertige B2B-Arbeitsoberfläche mit klarer Informationshierarchie.
- Neutraler Graphit-/Schwarzraum mit kühlem Eisblau und Silber als Akzent.
- Sichtbare räumliche Tiefe und Atmosphäre, ohne Effekthascherei.
- Daten bleiben schneller erfassbar als die visuelle Inszenierung.
- Dunkel ist der einzige aktive Modus; Tokens müssen einen späteren Hellmodus erlauben.

## Gestaltungsprinzipien

1. Erst Aufgabe und Informationshierarchie, dann Oberfläche.
2. Flächen durch Abstand, Linien und Tonwert trennen; nicht alles in Karten setzen.
3. Primäraktionen deutlich, Nebenaktionen ruhig und reversibel gestalten.
4. Status immer zusätzlich durch Text vermitteln, nie ausschließlich durch Farbe.
5. Dichte an Scan-Aufgabe und Datenmenge ausrichten, nicht an Showcase-Screenshots.

## Tokens

- Farben ausschließlich über semantische CSS Custom Properties definieren.
- Keine beliebigen Hex-, RGB- oder OKLCH-Werte direkt in Komponenten ergänzen.
- Surface-Stufen: `surface-0` Hintergrund, `surface-1` Shell, `surface-2` Kontrolle,
  `surface-3` aktiver oder angehobener Zustand.
- Linien: `line-soft`, `line`, `line-strong`.
- Text: `ink`, `muted`; Akzente: `ice`, `ice-strong`, `silver`.
- Semantik: `success`, `warning`, `danger`.
- Radien: klein 7 px, mittel 11 px, groß 16 px.
- Schatten: Stufe 1 Kante, Stufe 2 Bedienfläche, Stufe 3 Hauptoberfläche.

## Typografie

- Bestehenden System-Font-Stack beibehalten.
- Überschriften mit enger Laufweite und klarer Gewichtung, nicht ultrafett.
- Fließtext kompakt und gut lesbar; keine dekorativen Versalien.
- Versalien nur für kurze Kicker, Labels und Tabellenköpfe einsetzen.
- Zahlen und Termine tabellarisch setzen, wenn sie untereinander verglichen werden.
- Inter, Poppins oder eine neue Webfont nicht ohne eigene Designentscheidung einführen.

## Layout

- Der Seitenrahmen trägt die Atmosphäre; Inhalte benötigen nicht jeweils eine Karte.
- Seitentitel, Zweck und Aktionen bilden eine klare Kopfzone.
- Filter bleiben sichtbar und stehen direkt vor der Ergebnisliste.
- Desktop nutzt Breite für eine Filterzeile; Tablet darf kontrolliert umbrechen.
- Mobile stapelt Bedienelemente und erlaubt horizontales Scrollen großer Datentabellen.
- Inhaltsbreite und Abstände müssen auch bei 5 und bei 60 Zeilen funktionieren.

## Datenlisten

- Tabellen bleiben Tabellen, wenn zeilenweises Überfliegen die Hauptaufgabe ist.
- Tabellenkopf bleibt beim vertikalen Scrollen sichtbar.
- Zeilen sind mittel-kompakt; Hover darf keine Lageverschiebung verursachen.
- Ist eine Zeile anklickbar, bleibt ein echter Link als Fallback vorhanden.
- Anklickbare Zeilen müssen Fokus, Enter und Leertaste unterstützen.
- Primärinformation beginnt jede Zeile; Metadaten sind sichtbar zurückgenommen.
- Spalten ohne unmittelbaren Scan-Wert gehören nicht in die Übersicht.

## Filter

- Fachdomäne und Status sind primäre Filter und visuell leicht hervorgehoben.
- Suche, Review und Geschäftswert bleiben dauerhaft sichtbar.
- Filterung wird explizit ausgelöst; keine versteckten automatischen Server-Requests.
- Zurücksetzen ist eine ruhige Textaktion, keine konkurrierende Hauptschaltfläche.
- Labels bleiben sichtbar; Placeholder ersetzen keine Feldbezeichnung.

## Status und Badges

- Badge-Flächen sind kompakt, leicht eckig und semantisch getönt.
- Keine leuchtenden Pillen und keine frei erfundenen Statusfarben.
- Phase nutzt Eisblau, bereit nutzt Grün, Prüfung nutzt Amber, blockiert nutzt Rot.
- Domänen bleiben neutral, damit Status in der Zeile priorisiert bleibt.

## Effektbudget

- Maximal drei Elevation-Stufen pro Ansicht.
- Erlaubt: statisches atmosphärisches Licht, feine Kanten, innere Highlights,
  kurze Hover-, Fokus-, Auswahl- und Statusübergänge.
- Animationen bevorzugen `opacity` und `transform`; Layout darf nicht springen.
- Keine dauerlaufenden Animationen, Partikelfelder, Canvas- oder WebGL-Effekte.
- Kein Effekt darf Textkontrast, Scangeschwindigkeit oder Klickziel verschlechtern.
- `prefers-reduced-motion` ist verpflichtend.

## Harte Verbote

- Kein zentrierter Hero aus Überschrift, Unterzeile und CTA.
- Kein Raster aus drei identischen Feature-Karten.
- Kein lila-blauer Verlauf als Markenabkürzung für „KI“.
- Keine gläsernen Karten auf jeder Ebene.
- Keine willkürlichen Farben, Schatten, Radien oder Icon-Stile.
- Keine neuen Bedienelemente als Attrappe für spätere Features.
- Kein Austausch funktionaler Links durch rein skriptbasierte Navigation.

## Accessibility und Stabilität

- Sichtbarer Fokus für alle interaktiven Elemente.
- Semantische Überschriften, Labels, Tabellenköpfe und Zeitangaben verwenden.
- Kontrast mindestens WCAG AA für normalen Text.
- Touch-Ziele in mobilen Ansichten mindestens etwa 42 px hoch.
- Inhalte ohne JavaScript weiterhin über echte Links erreichbar halten.
- Bestehende URLs, Berechtigungen und Serverlogik bei rein visuellen Arbeiten bewahren.

## Abnahme

- Wirkt die Ansicht klar hochwertiger und weniger generisch?
- Findet man Fachdomäne, Status, Reife und nächste Entscheidung beim Überfliegen?
- Funktionieren Filter, Zeilenklick, Tastatur und echter Link?
- Bleiben Effekte stabil und verdecken keine Information?
- Ist der Seitenrahmen in sich konsistent?
- Funktioniert die Ansicht auf Desktop, Tablet und Mobile?
- Sind bestehende fachliche Funktionen vollständig erhalten?

## Branch-Regel

Das bestätigte Design wird auf `agent/ui-vnext-full` konsistent auf alle Seiten
übertragen. Auf `main` sind Selbst-Ausnahmen nicht zulässig; dort braucht jede
Abweichung von diesem Dokument eine ausdrückliche Freigabe.
