# Portfolio Dashboard – Review-Checkliste

Kurze manuelle Prüfung für Review/Merge des Portfolio-Cockpit-Umbaus.

## 1) Primärpfad / Navigation

- [ ] Dashboard mit gültigem `personId` öffnen.
- [ ] Neues Portfolio-Cockpit ist direkt sichtbar (nicht hinter Legacy versteckt).
- [ ] Legacy-Analytics sind vorhanden, aber sekundär (einklappbarer Bereich).

## 2) Holdings-Selektion / Detailfluss

- [ ] Holdings-Liste zeigt Datenstatus lesbar (z. B. `OK`, `Preis-Fallback`).
- [ ] Klick auf eine Holding markiert aktive Zeile.
- [ ] Instrument-Detailpanel folgt der Auswahl (Symbol/Name aktualisiert sich).
- [ ] Bei leerer Holdings-Liste erscheint ein klarer leerer Zustand statt fehlerhafter Anzeige.

## 3) Performance / Benchmark

- [ ] Performance-Summary zeigt `Start`, `Ende`, `Veränderung`, `Rendite`.
- [ ] Portfolio- und Benchmark-Darstellung sind visuell unterscheidbar.
- [ ] Wenn Benchmarkdaten fehlen, erscheint ein sauberer Fallback-Hinweis statt Fehlerblock.

## 4) Risk / Coverage

- [ ] Risk-Panel zeigt vorhandene Werte für Volatilität/Drawdown/Konzentration.
- [ ] Additive Felder (`Korrelation`, `Beta`, `Tracking Error`) werden angezeigt, falls vorhanden; sonst `n/a`.
- [ ] Coverage-Banner zeigt fehlende Daten und Fallback-Hinweise verständlich und ohne rohe Debug-Texte.

## 5) Robustheit

- [ ] Seite bleibt stabil bei partiellen Datenlücken (fehlende Preise, fehlende Klassifikationen).
- [ ] Keine unerwarteten Fehlermeldungen bei Wechsel der selektierten Holding.
- [ ] Legacy-Bereich kann geöffnet werden, ohne den Primärpfad zu stören.

## 6) Optional: schnelle technische Checks

- [ ] Frontend-Tests für Dashboard-Module laufen lokal (Vitest), sofern Tooling vorhanden.
- [ ] Keine offensichtlichen Konsolenfehler bei Cockpit-Interaktion.
