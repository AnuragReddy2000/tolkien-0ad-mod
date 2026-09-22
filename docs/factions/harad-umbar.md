# Harad & Umbar — Detailed Design

## Identity

Harad & Umbar are desert and coastal raiders. They combine mobility, poison attrition, corsair economics, naval harassment, and Mûmakil warfare.

## Corsair Plunder versus ordinary loot

Standard 0 A.D. loot is a general reward for eligible kills. Corsair Plunder is a separate faction mechanic that can reward profitable targets and extend to buildings.

Harad should receive only a fraction of the value of destroyed military units, ships, siege engines, and selected buildings. Workers, farms, houses, and low-value structures should provide little or no special plunder. Fixed reward bands may be easier to implement than reading exact construction costs.

Plunder creates momentum but must not refund the full enemy economy or become an infinite resource loop.

## Poison

Harad skirmishers and selected units use poison damage over time. Poison should reduce initial impact where necessary, be stronger against lightly armoured targets, and remain counterable by killing the unit, moving away, using armour, and applying support. It should not be universal.

## Mûmakil

Mûmakil use the established Indian war-elephant model as the implementation reference:

- very high health;
- large footprint;
- Crush/trample power;
- slow turning and high cost;
- significant population cost;
- vulnerability to focused ranged fire, siege, and anti-large tactics.

A Mûmakil can garrison a small group of archers in its howdah, initially around 3–4. Garrisoned archers receive extended line of sight and a modest range bonus, around 10–20%. They can fire while the Mûmakil moves if supported by the engine.

Damage to the Mûmakil should threaten the garrison. When the elephant dies, surviving crew should be exposed rather than safely disappearing. Empty Mûmakil emphasize trampling; garrisoned Mûmakil trade some concentration risk for mobile ranged pressure.

## Wonder and heroes

The Great Obsidian Palace should provide a local or focused Mûmakil bonus such as howdah range, trample quality, or modest health—not a stack of global speed and health bonuses.

The Black Serpent supports poison and ranged pressure. Castamir supports Corsair ships. Suladân supports Mûmakil and movement without making regeneration overwhelming.

## Weaknesses

Harad is vulnerable when mobility is denied, when plunder momentum is interrupted, and when expensive elephants are isolated or trapped in static siege warfare.
