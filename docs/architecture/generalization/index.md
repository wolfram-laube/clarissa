# CLARISSA – Generalisierung und NSAI-Regelwerk

Gesprächsnotizen vom 31.10.2026 (Sprachsession, Samstagabend)

## Ausgangsfrage

Wie generisch soll CLARISSA gebaut werden, damit es auch außerhalb der Öl- und Gasindustrie einsetzbar ist, ohne in Overengineering („eierlegende Wollmilchsau“) abzurutschen?

## Mögliche weitere Anwendungsfelder

- **Geothermie und CO2-Speicherung** – physikalisch fast identisch mit Reservoirsimulation, starker Markt mit Fördergeldern, in Österreich und Bayern aktuell. Naheliegendster zweiter Use Case.
- **Hochwasser- und Grundwassermodelle** – für Gemeinden und Behörden, „Was wäre, wenn“-Fragen durch Nicht-Experten.
- **Krankenhausmanagement** – Bettenbelegung, OP-Kapazitäten. Andere Simulationsart (ereignisdiskret statt Strömungsphysik), Architekturmuster passt aber. Vorerst nur als Pitch-Folie.

## Architekturempfehlung: schmal generisch

- CLARISSA zuerst konsequent für Öl und Gas fertigstellen.
- Genau zwei Plugin-Punkte einziehen:
    1. **Simulator-Adapter** (Eclipse, tNavigator, später z. B. Geothermie-Tool). Schnittstelle relativ klar: Eingabedeck rein, Ergebnisse raus.
    2. **Regelwerk-Adapter für den NSAI-Layer** als austauschbares Domänenpaket.
- Beide Schnittstellen so schmal wie möglich, mit jeweils genau einer Implementierung (Eclipse, Öl-Regelpaket).
- Erweitern erst, wenn ein zweiter realer Use Case kommt. Generalisierung aus zwei echten Fällen ableiten, nicht aus Gedankenexperimenten.
- Gegen den Overengineering-Reflex: Die Wollmilchsau als Zielbild in einem ADR festhalten, aber nur das bauen, was der aktuelle Fall braucht.

## NSAI-Regelwerk: keine eigene DSL

- Eigene DSL oder globale Grammatik bedeutet Parser, Fehlermeldungen, Doku, Tooling – man baut eine Sprache statt eines Produkts.
- Stattdessen bestehende Formalismen nutzen:
    - Python-Funktionen mit fester Signatur plus Metadaten (Name, Begründung, Schweregrad) – einfachster Start
    - Datalog für logische Regeln
    - SMT-Solver (z. B. Z3) für numerische Constraints
    - SHACL, falls Richtung Wissensgraph

## Regeln durch Fachleute: natürliche Sprache als DSL

- Kernidee von CLARISSA: Nicht nur Spezialisten sollen arbeiten können. Komplexität darf nicht einfach in den NSAI-Layer verschoben werden.
- Lösung: Reservoir-Ingenieur formuliert Regeln in natürlicher Sprache, ein LLM übersetzt in einen bestehenden Formalismus.
- **Problem:** Der NSAI-Layer ist das Sicherheitsnetz gegen LLM-Fehler. Schreibt ein LLM die Regeln, prüft der Bock den Gärtner.
- **Sicherungen:**
    1. Rückübersetzung der formalen Regel in Klartext, Bestätigung durch den Ingenieur
    2. Jede Regel wird vor dem Scharfschalten gegen bekannte gute und schlechte Beispielfälle getestet

## Dialectic AI als Kontrollinstanz

- Bestehender Ansatz: zwei verschiedene LLMs diskutieren, Übernahme nur bei ca. 90 % Übereinstimmung.
- Erhöht die Wahrscheinlichkeit korrekter Ergebnisse, aber weniger als intuitiv erwartet, weil die Fehler korreliert sind (ähnliche Trainingsdaten, gemeinsame blinde Flecken).
- Korrelation senken:
    - Modelle aus möglichst verschiedenen Familien
    - Ein Modell in explizit gegnerischer Rolle („finde den Fehler“ statt „bewerte das“)
    - **Dritter, nicht-LLM-basierter Prüfer:** z. B. ein kleiner Simulationslauf, der die Regel an echten Daten testet – „Dialectic AI mit einem Teilnehmer, der nicht diskutiert, sondern rechnet“

## Offene Fragen

- Wie genau wird die 90-%-Übereinstimmung in Dialectic AI gemessen?
- Welcher Formalismus für das erste Öl-Regelpaket?
- Wie sieht der rechnende dritte Prüfer konkret aus (Surrogatmodell, Mini-Simulation, Testdatensatz)?

## Nachtrag 01.11.2026: Akronym KCT

KCT benennt die Ausbaustufe der NSAI-Komponente nach dem KAN-Paper.

| Buchstabe | Bedeutung | Rolle |
| --- | --- | --- |
| K | Kolmogorov-Arnold-Netzwerke (KAN) | Technische Basis der NSAI-Komponente |
| C | Causal Reasoning | Einzuhaltendes Paradigma: Wirkzusammenhänge statt Korrelationen |
| T | Thousand Brains (Hawkins) | Cortical Columns, passt zur Dialectic AI |

Q-KCT bezeichnet die spätere Quantum-Ausbaustufe (Quantum-KANs). Das Q steht bewusst vorne und abgesetzt: KCT ist der Kern, Q-KCT ein Ausblick, solange die Hardware fehlt.

## Module

Die Adapter sind eigenständige Module in Unterordnern. Jedes lässt sich allein als PDF bauen; das Gesamt-PDF bindet sie über `pandoc.yaml` ein, ohne Kopien.

- [Simulator-Adapter](simulator-adapter/index.md)
- [NSAI-Regelwerk-Adapter](nsai-adapter/index.md)
- [Dialectic-AI-Adapter](dialectic-ai-adapter/index.md)
