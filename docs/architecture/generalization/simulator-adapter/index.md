# CLARISSA – Simulator-Adapter

Modul des Zentraldokuments [Generalisierung](../index.md).

## Zweck

Der Simulator-Adapter ist eine der zwei schmalen Plugin-Schnittstellen von CLARISSA. Er kapselt die Anbindung an Reservoir-Simulatoren, sodass der Kern von CLARISSA nicht an einen bestimmten Simulator gebunden ist.

## Aktuelle Anbindungen

- Eclipse
- tNavigator

## Rolle bei der Generalisierung

CLARISSA wird zuerst vollständig für Öl und Gas gebaut. Für spätere Use Cases (Geothermie und CO2-Speicherung, Hochwasser- und Grundwassermodelle, Krankenhausmanagement) wird nur ein neuer Simulator-Adapter benötigt, kein generisches Framework.

## Offene Punkte

- Schnittstellendefinition (Eingaben, Ausgaben, Fehlerfälle)
- Sequenzdiagramm in Mermaid
