# Angmar

## Identity

Angmar is a dark northern faction focused on fear, cold, and temporary necromantic reinforcement. It should feel oppressive and sinister without becoming a permanent free army generator.

## Core mechanics

### Iron Crown Frost
Enemies attacking Angmar structures or units in close melee take a temporary attack-speed reduction. It is a local battlefield pressure effect, not a universal debuff. Finalized: -10% attack speed for 3s on melee contact, no heavy stacking. Active v0.2: -8% for 3s.

### Barrow Plague
Enemy military deaths inside the aura of an Angmar Temple, Dark Temple, or Witch-Fortress have a chance to rise as weak Undead Thralls under Angmar's control. Conversion chance is about 15% for ordinary military units; larger units receive reduced conversion. Heroes, workers, summoned units, and Angmar units are not eligible. v1 20% shelved.

Thralls decay after about 45 seconds and can be controlled. They are weak, temporary, and cannot gather or build. Finalized: ~40–50% HP, ~50–65% attack, very low armor, slightly slow, no cost but no pop either; controllable military-only (move/attack/patrol/guard — no gather/build/repair/garrison/capture/heal-to-permanent/chain-convert); HP-decay + 45s TTL; champions/siege 5–10%; one roll per death (seeded RNG, never Math.random). No hard pop cap — deaths × 15% × 45s is the natural cap + one-corpse-one-roll safeguard.

## Cavalry

A dark mirror of Arnor's horse tradition (per `cavalry_recommendations.md`):
- Scourge Scout — Phase I light cavalry mapping/harass.
- Rhudaur Mercenary Cavalry — Phase II medium javelin/sword raiders, aggressive and versatile.
- Black Númenórean Knights — Phase III champion heavy melee cavalry, built to answer Gondor's heavy armor lines. Trains at Raider Pens (Stable) / Witch-Fortress; strict pop cap.

## Siege (per `siege_recommendations.md`)

Built for multi-century attrition against fortified Arnorian cities and watchtowers.
Finalized: full access to heavy iron-clad Siege Towers + massive Catapults; catapult upgrade to fling disease-ridden debris or flaming pitch dealing damage-over-time to garrisons and structures. Champion Snow Troll + Rogrog crush aura supplement, not replace, this mechanical core.

## Strengths

- battlefield control through fear and cold
- temporary battlefield reinforcement
- sinister late-game aura effects
- strong local defense and temple-driven style

## Weaknesses

- weaker when forced into open-field equal-unit battle
- dependent on battle aura and nearby structures
- less mobile than cavalry or raiding factions

## Structures

- dark temple; witch-fortress; cold fortifications; worker and levy structures; strongholds and control points.

Finalized tree (kept): Phase I — Dark Citadel, Thrall Huts, Resource Pit, Scavenger Yard, Frozen Field, Outpost. Phase II — Iron Barracks, Raider Pens (Stable), Sorcerous Forge, Market, Spired Watchtower, Frost Wall. Phase III — Witch-Fortress, Dark Temple, Carn Dûm.

## Units

- levy infantry; dark melee units; sorcerous command units; mountain troll or monster support; ranged and anti-armour support.

Finalized: Rhudaur Hillmen Levy (exclusive worker + levy), Angmar Orc Spearmen (basic), Angmar Slasher (melee/skirmisher), Champion Snow Troll (anti-structure crush monster), Sorcerous Captain (elite support-caster). Scourge Scout (Phase I light cav), Rhudaur Mercenary Cavalry (Phase II medium raiders), Black Númenórean Knights (Phase III champion heavy cav).

## Heroes

- Witch-king; Hwaldar; a troll chieftain or dark commander. Hero roles should support fear, local control, or monster leadership.

Finalized (local): Witch-king (fear aura cutting nearby enemy damage/morale, no auto-panic), Hwaldar (+move +gather for Hillmen), Rogrog (+structural crush for Snow Trolls).

## Wonder

Carn Dûm creates a local cold shroud that reduces visibility and enemy firing range near the base. It should remain regional, not map-wide. Finalized: -30% invader visibility/range over local base only.

## Counterplay

Break the aura area, force Angmar into open battle, deny the temple network, and use ranged pressure to prevent the undead reinforcement cycle from establishing momentum.
