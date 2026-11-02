# CLARISSA – NSAI-Regelwerk-Adapter

Modul des Zentraldokuments [Generalisierung](../index.md).

## Zweck

Der NSAI-Regelwerk-Adapter ist die zweite schmale Plugin-Schnittstelle von CLARISSA. Er bindet die neurosymbolische Validierung an, die Ergebnisse von LLM und RL gegen fachliche Regeln prüft.

## Regeldefinition

Fachexperten formulieren Regeln in natürlicher Sprache, statt eine eigene DSL zu lernen. Ein LLM übersetzt sie in bestehende Formalismen, etwa Python-Funktionen, Datalog, Z3 oder SHACL.

## Absicherung gegen Zirkularität

Wenn ein LLM die Regeln schreibt, die LLM-Fehler abfangen sollen, bewacht der Fuchs den Hühnerstall. Deshalb:

- Rückübersetzung jeder formalen Regel in Klartext zur Bestätigung durch den Ingenieur
- Test jeder Regel gegen bekannte gute und schlechte Beispiele vor der Aktivierung
- Dialectic AI: zwei unabhängige Modelle müssen sich einigen (siehe [Dialectic-AI-Adapter](../dialectic-ai-adapter/index.md))

## Abgrenzung

Keine zusätzlichen GAN-Ansätze, da Dialectic AI die Funktion bereits abdeckt. Goodfellow wird im Related-Work-Abschnitt gewürdigt.

## Offene Punkte

- Schnittstellendefinition
- Auswahl des Regel-Formalismus
- Sequenzdiagramm in Mermaid
