export const GLOSSARY: Record<string, string> = {
  // Bilanz / Balance Sheet
  totalAssets:
    'Bilanzsumme – Gesamtvermögen des Unternehmens. Summe aller Besitztümer, Forderungen und liquiden Mittel.',
  totalCurrentAssets:
    'Kurzfristiges Umlaufvermögen – Vermögenswerte, die innerhalb eines Jahres in Geld umgewandelt werden können (Bargeld, Forderungen, Vorräte).',
  totalLiabilities:
    'Gesamtverbindlichkeiten – alle Schulden des Unternehmens gegenüber externen Gläubigern.',
  totalCurrentLiabilities:
    'Kurzfristige Verbindlichkeiten – Schulden, die innerhalb eines Jahres fällig sind.',
  totalEquity:
    'Eigenkapital – Anteil der Aktionäre am Unternehmensvermögen nach Abzug aller Schulden. Formel: Bilanzsumme minus Gesamtschulden.',
  cashAndCashEquivalents:
    'Kassenbestand & Geldäquivalente – sofort verfügbare liquide Mittel.',
  cashAndShortTermInvestments:
    'Liquiditätsreserven – Kassenbestand plus kurzfristige Geldanlagen.',
  totalDebt:
    'Gesamtschulden – Summe aus kurz- und langfristigen Verbindlichkeiten gegenüber Kreditgebern.',
  netDebt:
    'Nettoverschuldung – Gesamtschulden abzüglich Liquiditätsreserven. Negativ bedeutet: mehr Cashreserven als Schulden.',
  shortTermDebt: 'Kurzfristige Finanzschulden – innerhalb eines Jahres fällige Verbindlichkeiten gegenüber Banken.',
  longTermDebt: 'Langfristige Finanzschulden – Anleihen und Kredite mit Laufzeit über einem Jahr.',
  accountsReceivable:
    'Forderungen aus Lieferungen – Geld, das Kunden dem Unternehmen noch schulden.',
  inventory: 'Vorräte – Rohstoffe, Halbfertigwaren und Fertigprodukte im Lager.',
  accountsPayable: 'Verbindlichkeiten aus Lieferungen – Rechnungen, die das Unternehmen noch bezahlen muss.',
  retainedEarnings:
    'Gewinnrücklagen – kumulierter, nicht ausgeschütteter Jahresüberschuss seit Unternehmensgründung.',
  goodwillAndIntangibles:
    'Firmenwert & immaterielle Vermögenswerte – Kaufpreisaufschläge aus Übernahmen und Patente, Marken, Software.',
  netPPE:
    'Sachanlagen (netto) – Maschinen, Gebäude, Fahrzeuge abzüglich kumulierter Abschreibungen.',
  workingCapital:
    'Working Capital – kurzfristiges Umlaufvermögen minus kurzfristige Verbindlichkeiten. Zeigt die kurzfristige Liquidität.',

  // GuV / Income Statement
  revenue: 'Umsatz – Gesamterlöse aus dem operativen Geschäft.',
  costOfRevenue:
    'Umsatzkosten – direkte Produktionskosten (Material, Fertigung). Differenz zum Umsatz ergibt den Bruttogewinn.',
  grossProfit: 'Bruttogewinn – Umsatz minus Herstellungskosten. Zeigt, wie profitabel die Produkte/Dienstleistungen an sich sind.',
  ebitda:
    'EBITDA – Gewinn vor Zinsen, Steuern, Abschreibungen. Misst die operative Ertragskraft unabhängig von Finanzierung und Bilanzierungswahlrechten.',
  ebit: 'EBIT – Gewinn vor Zinsen und Steuern (operatives Ergebnis).',
  operatingIncome: 'Betriebsergebnis (EBIT) – Gewinn aus dem Kerngeschäft vor Zinsen und Steuern.',
  netIncome: 'Jahresüberschuss – Gesamtergebnis nach Steuern und Zinsen.',
  interestExpense: 'Zinsaufwand – Kosten für die Finanzschulden des Unternehmens.',
  taxProvision: 'Steuerrückstellungen – gebuchter Steueraufwand für die Periode.',
  epsDiluted:
    'Verwässerter Gewinn je Aktie (EPS) – Jahresüberschuss geteilt durch alle ausstehenden Aktien (inkl. Wandelanleihen, Optionen).',

  // Margen
  grossMargin:
    'Bruttomarge – Bruttogewinn / Umsatz. Zeigt, wie viel nach den direkten Herstellungskosten übrig bleibt.',
  operatingMargin:
    'Operative Marge – Betriebsergebnis / Umsatz. Je höher, desto effizienter das Kerngeschäft.',
  netMargin:
    'Nettomarge – Jahresüberschuss / Umsatz. Der Anteil des Umsatzes, der als Gewinn bei den Aktionären landet.',
  ebitdaMargin: 'EBITDA-Marge – EBITDA / Umsatz.',

  // Cashflow
  operatingCashFlow:
    'Operativer Cashflow – tatsächlich erwirtschafteter Zahlungsüberschuss aus dem laufenden Geschäft.',
  capitalExpenditure:
    'Investitionsausgaben (CapEx) – Ausgaben für Maschinen, Gebäude, Software – Investitionen in die Zukunft.',
  freeCashFlow:
    'Freier Cashflow – operativer Cashflow minus CapEx. Das Geld, das dem Unternehmen tatsächlich "frei" zur Verfügung steht für Dividenden, Schuldenabbau oder Aktienrückkäufe.',
  dividendsPaid: 'Ausgeschüttete Dividenden – Zahlungen an die Aktionäre in der Periode.',
  shareRepurchase:
    'Aktienrückkäufe – Ausgaben für den Rückkauf eigener Aktien. Erhöht den Gewinn je Aktie für verbleibende Aktionäre.',

  // Kennzahlen / Ratios
  roe: 'Return on Equity (ROE) – Eigenkapitalrendite. Zeigt, wie effizient das Management das Aktionärskapital einsetzt. Formel: Jahresüberschuss / Eigenkapital.',
  roa: 'Return on Assets (ROA) – Gesamtkapitalrendite. Wie profitabel nutzt das Unternehmen seine gesamten Vermögenswerte? Formel: Jahresüberschuss / Bilanzsumme.',
  debtToEquity:
    'Verschuldungsgrad (D/E) – Gesamtschulden / Eigenkapital. Hohe Werte = höheres Finanzrisiko, aber auch potenziell höhere Eigenkapitalrendite (Leverage-Effekt).',
  currentRatio:
    'Current Ratio (Liquiditätsgrad 2) – kurzfristiges Umlaufvermögen / kurzfristige Verbindlichkeiten. Werte über 1,0 bedeuten: das Unternehmen kann kurzfristige Schulden aus dem Umlaufvermögen decken.',
  trailingPe:
    'Kurs-Gewinn-Verhältnis (KGV, trailing) – Aktienkurs / Gewinn je Aktie der letzten 12 Monate. Misst die Bewertung relativ zum erzielten Gewinn.',
  forwardPe:
    'Forward KGV – Aktienkurs / geschätzter zukünftiger Gewinn je Aktie. Zeigt die Bewertung auf Basis von Analystenschätzungen.',
  priceToBook:
    'Kurs-Buchwert-Verhältnis (KBV) – Marktkapitalisierung / Buchwert des Eigenkapitals. Werte unter 1 können auf eine Unterbewertung hindeuten.',
  beta: 'Beta – Maß für die Schwankungsintensität einer Aktie im Vergleich zum Gesamtmarkt. Beta > 1: schwankt stärker als der Markt.',
  dividendYield:
    'Dividendenrendite – jährliche Dividende / Aktienkurs. Zeigt den laufenden Ertrag einer Aktie als Prozentzahl.',
  marketCap: 'Marktkapitalisierung – aktueller Börsenwert des Unternehmens (Kurs × Anzahl Aktien).',
  enterpriseValue:
    'Unternehmenswert (EV) – Marktkapitalisierung plus Nettoverschuldung. Der "Kaufpreis" des gesamten Unternehmens unabhängig von der Finanzierungsstruktur.',

  // ETF-spezifisch
  aum: 'Assets under Management (AUM) – gesamtes verwaltetes Fondsvermögen.',
  ter: 'Total Expense Ratio (TER) – jährliche Gesamtkosten des Fonds in Prozent des Fondsvermögens. Wichtig für den Langzeitvergleich.',
  expenseRatio: 'Kostenquote – jährliche Verwaltungskosten des ETFs in Prozent des Fondsvermögens (äquivalent zur TER).',
  fundYield:
    'Ausschüttungsrendite – jährliche Ausschüttungen des ETFs in Prozent des aktuellen Kurses.',
  inceptionDate: 'Auflagedatum – wann der ETF zum ersten Mal gehandelt wurde. Jüngere ETFs haben weniger historische Daten.',
  fundFamily: 'Fondsgesellschaft – der Emittent / Anbieter des ETFs.',
  topHoldings: 'Top-10-Positionen – die größten Einzeltitel im ETF nach Gewichtung.',
  sectorWeights: 'Sektoraufteilung – Anteil verschiedener Branchen am ETF-Portfolio.',
  assetClasses: 'Asset-Klassen – Aufteilung des ETFs nach Anlageklassen (Aktien, Anleihen, Cash).',
  ytdReturn: 'Year-to-Date-Rendite – Kursentwicklung des ETFs seit Jahresbeginn.',
  threeYearReturn: '3-Jahres-Rendite (p.a.) – durchschnittliche jährliche Rendite der letzten 3 Jahre.',
  fiveYearReturn: '5-Jahres-Rendite (p.a.) – durchschnittliche jährliche Rendite der letzten 5 Jahre.',
}
