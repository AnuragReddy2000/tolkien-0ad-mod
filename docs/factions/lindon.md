# Lindon

## Identity

Lindon is an elite maritime and disciplined infantry faction. It should feel refined, expensive, resilient, and tactically strong when given time and coast.

## Core mechanics

### Gift of the West
Selected technologies research faster. This should be a narrow, meaningful bonus to high-craft, naval, or defensive techs rather than a universal acceleration of every upgrade.

Implemented: a 15% research-time reduction applies to the Dock, defensive
structures, and Forge. It is not a universal research-speed bonus.

Healing (narrow exception, outside combat only, small radius, stops when damaged):
Docks repair/heal ships; Temples heal organics; Fortresses stronger local heal; Outposts none or very weak after tech. Rate 0.5–1%/s, not v1 2%/s.

Implemented: idle-regeneration auras, radius 25, combat stops regen — Dock
+0.5 HP/s to Ships, Temple +0.75 HP/s to organics, Fortress +1 HP/s to
organics. Outposts have no healing aura.

### Noldorin Metallurgy
Implemented: the Blacksmith technology grants Champions +1 Pierce attack
damage. It does not grant Pierce armour.

### Cavalry (restricted)
Lindon fields light border horsemen only — no shock or champion cavalry. Horses serve communication, redeployment, and light skirmish (per `cavalry_recommendations.md`).

Implemented: Mithlond Border Rider is light cavalry for scouting and
skirmishing, not shock or champion cavalry.

### Swan Ships
Swan Ships provide maritime reinforcement, transport, or coastal support. They are not a free infantry factory. They should feel expensive and special.

Current implementation: Phase II transport with capacity for 20 infantry;
eligible infantry may be trained aboard at full cost. It does not require
the ship to be undamaged or near a friendly Dock, Civic Centre, Fortress, or
beachhead to train. There is no additional per-ship lifetime training limit or
cooldown; normal resource/population costs and the standard training queue
apply. Shoreline disembarkation behavior still needs in-game verification.

## Strengths

- high-quality infantry and navy
- strong coastal operations
- good defensive and research identity
- resilient elite units with high value

## Weaknesses

- slower replacement and less scalability than mass factions
- vulnerable to attrition if the player cannot hold the coast or control the battlefield
- best when given time and space to develop

## Structures

- civic center; houses; docks; workshop or high-craft facilities; strongholds; towers; watch structures; relevant elite barracks.

Finalized tree (kept from v1): Phase I — CC, House, Storehouse, Farmstead, Field, Outpost, Wooden Palisade, Dock. Phase II — Barracks, Market, Blacksmith, Defense Tower, Stone Wall, Sentry Post, Rider's Lodge (Stable, light cav only). Phase III — Fortress, Temple, Wonder (White Towers of Elostirion).

## Units

- elite infantry; archers; marine or coast-focused infantry; a naval core; a high-quality supporting ranged line.

Finalized: Spearmaiden (Wood/Food), Archer (Stone/Metal), Fishing Boat, Trade Caravan, Merchant Ship, Fire Galley; Champions Noldorin Phalanx (elite spear) + Mithril-clad Swordsman (late champion). Expensive, low numbers, slow replacement. Mithlond Border Rider (Phase II light cav skirmisher, Rider's Lodge only).

### Siege (per `siege_recommendations.md`)
No heavy structural catapults — clear-cutting forests for clunky wooden engines is antithetical to Elven culture.
Finalized: highly precise elegant Elven Bolt-Throwers to snipe high-value targets and disable enemy siege engines (not wall-breakers); walls brought down via elite Infantry Vanguard Saboteurs (implemented: Fortress, Phase III, crush-only vs structures, cannot attack units) or Singing-arrows Forge tech (implemented: Bolt-Throwers +20% pierce, Saboteurs +25% crush).

## Heroes

- a naval or command hero; an elite commander with range or support role; a local morale or support buff, not a global all-unit buff.

Finalized (localized only): Círdan (naval speed + garrison support), Gil-galad (nearby Phalanx +Pierce + trample resist), Elrond (front-line swordsman + Vilya healing aura for nearby infantry; active click-heal removed). All three are Fortress heroes and inherit the standard 0 A.D. Hero category match limit, which allows only one Hero to be trained per match.

## Wonder

A wonder that works on land and sea without becoming a universal combat answer is preferred over a broad map-wide reveal or an all-unit combat boost.

Finalized — Arches of the Last Shore (The Haven Keep): grace of the West. While the completed Arches stand in Lindon hands, 15% of each fallen Lindon unit's cost (floored per resource) returns to the treasury. Units only — heroes, structures, foundations, and the wonder itself grant nothing. Raze it to end the grace. Implemented in `LastShore.js` and verified in-game (0.28.0 headless with a temporary probe driver, since removed).

Verified mechanism: the death signal is `OnGlobalOwnershipChanged(to=INVALID_PLAYER)` on the wonder (0.28 has no global EntityKilled message). The broadcast fires exactly once per destroyed entity at end-of-turn deferred deletion, before `OnDestroy`, with Identity/Cost/Health still queryable. Combat kills and `Health.Kill()` destroy at 0 HP; promotion replacement, delete/cheat removal, and defeat cleanup destroy at full HP — a `health==0` guard cleanly separates true deaths. Capture moves ownership without destruction, so captured units never trigger it. Verified payouts: a completed Lindon-owned arch pays 6 food/6 wood per 45f/40w/5m spearman (metal floors to 0), exactly once per unit loss, and nothing for heroes, structures, alive removals, promotions, units owned by another player at death, foundation arches (foundation entities do not carry the component), non-Lindon-owned arches, or the wonder itself. Arch state is read at death-processing time (end of turn); multiple standing arches each pay independently.

Shelved: White Towers of Elostirion maritime-vision wonder (vision 200 + fleet +20% aura; too dead on land-locked maps — `lindon_elostirion_watch.json` now unreferenced).

## Counterplay

Pressure Lindon before its research cycle completes, deny coastal access, and force it into battles where its elite quality does not outweigh the enemy’s numbers or terrain control.

## Balance notes

The faction should be expensive to expand but highly effective in prepared fights. High quality is its strength, not raw numerical superiority.
