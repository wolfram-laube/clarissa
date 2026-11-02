# CLARISSA – Dialectic-AI-Adapter

Modul des Zentraldokuments [Generalisierung](../index.md).

## Zweck

Der Dialectic-AI-Adapter lässt mehrere unabhängige Modelle eine Aussage prüfen. Eine Schlussfolgerung gilt erst, wenn sich die Modelle einig sind (Zielwert etwa 90 % Übereinstimmung). Eine funktionierende Implementierung gibt es bereits.

## Rolle in CLARISSA

Dialectic AI sichert unter anderem das NSAI-Regelwerk ab: Wenn ein LLM Regeln formuliert, prüft ein zweites, unabhängiges Modell sie gegen.

## Abgrenzung

Keine zusätzlichen GAN-Ansätze, weil Dialectic AI die gegnerische Prüfung schon abdeckt. Goodfellow wird im Related-Work-Abschnitt als Vorbild gewürdigt. Thousand Brains (Hawkins) ist als Ausblick mit Dialectic AI verknüpft.

## Offene Punkte

- Schnittstellendefinition
- Unabhängigkeit der Prüfer: Modelle aus verschiedenen Familien?
- Ein Modell in ausdrücklich gegnerischer Rolle („finde den Fehler“)?
- Dritter Prüfer ohne LLM, etwa ein kleiner Simulationslauf?
- Sequenzdiagramm in Mermaid
