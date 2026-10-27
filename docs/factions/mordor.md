# Mordor

## Identity

Mordor is an industrial darkness faction. It values numbers, economy, attrition, and territorial corruption.

## Core mechanics

### Snaga Slaves
Snaga Slaves are the primary workers. Their presence should shape early-game economy and force the opponent to respond to worker protection and harassment.

Finalized: Snaga only Gatherer/Worker; all military omits Gatherer (AI forced to Snaga); cheap, fast-built, defenseless, disruptable. 3-to-1 numbers needed vs elites.

### Blighted Desolation
Enemy workers gathering within Mordor-controlled territory suffer a
territory-wide gather-rate penalty. This is a strategic effect, not a
farm-destruction mechanic, and does not vary by distance from a Mordor structure.

Current implementation: -15% enemy worker gather efficiency inside Mordor
territory, with a small spillover; it affects gathering only, does not destroy
nodes, does not stack, and does not affect Mordor workers.

### Crebain and Variag
Crebain provide reconnaissance and sight. Mordor fields no Wargs or Warg Riders (lore gap fix): its only cavalry are hired Variag horse-archers of Khand, frequently in Mordor's pay.

Finalized: Crebain (one fast flying scout flock at a time, large LOS, no attack, vulnerable to ranged units; ordinary vision does not reveal Doriath's concealed units unless they break camouflage by moving, attacking, or taking damage) + Variag Rider (hired citizen-cavalry archer trained at the Civic Centre — Mordor's only cavalry; no stable; skirmishes vs workers/isolated, weak spears/formations/forts).

Olog-hai are implemented champion trolls. Their Morgul Dread aura currently
slows nearby enemy attack cadence. The same dread rides with the Mordor heroes,
stronger. Armour reduction is intentionally excluded: dread weakens attack
cadence, while adding armour reduction would compound the aura with extra
damage vulnerability.

### Hordes of Mordor
+10% maximum population limit (e.g. 330 instead of 300), auto-granted
like vanilla Han / Mauryas / Persians. The horde fields more bodies,
not better bodies — Orc quality stays low by design.

### All-Seeing Eye
The Eye is a powerful information tool on a long cycle. The current
implementation searches selected enemy locations; it does not reveal the
entire map.

Finalized search-only: ~30–45s rotating regional search via short-lived seer entities on a fixed waypoint schedule (reveals units/structures/concealed in each visited region), ~8-min cooldown, global audio/visual warning ("The Eye Opens"), Barad-dûr must stand. Waypoints prioritize enemy heroes, fortresses, civic centres, and wonders — the Eye is drawn to strength. No global map reveal: Sauron's attention is finite (the lore reason the Ring could slip through), and the engine has no shroud-reveal API. Earlier hybrid (5s global + search) and timed-global fallbacks shelved.

### Siege (per `siege_recommendations.md`)
Industrial + biomechanical mix — slave labor, dark smithing, and war-beasts (engines of Minas Tirith).
Finalized: standard heavy catapults + Grond as signature Phase III champion ram + dual-mode Mountain Trolls (see Units). No elegant precision role — overwhelming attrition instead.

## Strengths

- cheap mass production
- strong pressure and attrition
- crebain scouting power
- oppressive territorial presence

## Weaknesses

- weaker in direct elite fights than armies built around quality
- vulnerable to cavalry, anti-large units, and static defensive play
- worker disruption can damage the economy sharply

## Structures

- dark fortresses; Orc and troll production; worker structures; towers; siege support; wonder site.

Finalized tree (kept): Phase I — CC, Slave Quarters, Orc Cookhouse, Field, Crude Palisade. Phase II — Breeding Pits (barracks: Orc foot, trolls, Crebain), Iron-works, Scaffolding Market, Watch-crag Tower, Crude Stone Wall. Phase III — Black Fortress, Dark Temple, Barad-dûr. No stable: Variag riders are hired at the CC.

## Units

- Snaga workers; Orcs; Orc archers; hired Variag horse-archers; heavy siege and troll-like support; dark elite infantry.

Finalized: Orc Warrior (baseline, cheap/fast, loses 1v1), Orc Archer, Variag Rider of Khand (hired citizen-cavalry archer, the only cavalry), Siege Catapult (standard heavy, massed slave-crewed), Grond Ram (unique Phase III Champion — slow-moving, beast-drawn, effective not free breach), Champion Uruk-hai Vanguard (stronger Orc, not answer-all), Olog-hai (champion troll with Morgul Dread), Mountain Troll (dynamic organic siege — switches boulder-throw ranged artillery / clubbing melee structural damage; metal-cheap bred beast from the Breeding Pits, weaker than the Olog-hai; dangerous, not invincible).

## Heroes

- Sauron; Gothmog; Khamûl. Khamûl leads scouting and raiding support. Saruman is reserved for alliance or scenario use instead of a standard Mordor hero.

Implemented trio: Sauron (area crush), Gothmog (nearby Orc attack-speed
support), and Khamûl (nearby Orc-class units gain movement speed and melee
damage). All three carry a stronger Morgul Dread than the Olog-hai's, slowing
nearby enemy attack cadence. Khamûl's Hunt is limited to those Orc-class
movement and melee-damage bonuses; additional bonuses against workers or
isolated targets are intentionally excluded.

## Wonder

Barad-dûr remains a major late-game information and battlefield control tool. The effect should be strong and noticeable but not permanent map control.

Implemented (slice): search-only Eye — a single seer entity hops between enemy strongholds (heroes, wonders, fortresses, civic centres first) on a fixed schedule, ~40s per search, ~8-min auto-cast cycle with a global warning; slaying the seer ends that gaze early. Barad-dûr art is a stand-in: Ptolemaic lighthouse mesh with fire props, re-skinned to the dark Kush stone texture (proper model deferred).

## Counterplay

Disrupt the worker economy, force Mordor to fight in a clean battle, and deny it the temporal advantages that let the attrition engine function.
