# Unit balance specification

**Version:** 1.3
**Baseline date:** 2026-10-27
**Engine target:** 0 A.D. 0.28
**Status:** Working v1.3 implementation baseline; effective-stat inventory and in-game validation remain open.

This is the canonical balance reference for the five implemented factions:
Doriath, Lindon, Mordor, Moria, and Númenor. The XML templates are the
authoritative gameplay source. `unit_stats.csv` is a convenience export and
must be regenerated or reconciled when templates change.

The remaining seven factions are future scope. Do not invent their final
numbers by extrapolating from the five-faction baseline. Add their archetypes
and role targets here when implementation begins.

## Version history

- v0.1 established first-pass numeric rosters.
- v0.2 recorded cross-faction tuning and implementation mappings, including
  engine-specific deviations and mechanics that were deferred.
- v0.3 standardized common attack cadence against 0 A.D. weapon archetypes.
- The 2026-10-20 rebalance pass established the current implemented combat
  stat baseline for the five factions.
- This v1.0 pass reconciles that baseline with templates, records agreed role
  changes, and identifies work that remains unimplemented or unverified.
- v1.1 (2026-10-24) Mordor lore pass: removed Warg, Warg Rider, and Morgul
  Knight; added Variag Rider (hired CC citizen-cavalry archer, no stable) and
  Olog-hai (Fortress champion troll); recosted Mountain Troll to 160/80/0/10
  (Barracks "Breeding Pits"); renamed the dread aura to Morgul Dread and added
  a stronger hero variant on all three Mordor heroes. XML, CSV, and faction
  docs reconciled; XML/JSON validation and promotion checks pass; in-game
  playtest pending.
- v1.2 (2026-10-24) Doriath forest-combat pass: implemented the deferred
  forest bonuses via a new `ForestAffinity` component (self-applied modifiers
  toggled by tree density, no core-component fork). Green-weave Scout, Doriath
  Hunter, Doriath Ranger, and March-warden gain +10% movement in forest. The
  Guard of the Caves' armour is now forest-conditioned: base reduced to
  3/3/13, +2 Hack/Pierce/Crush while in forest (5/5/15). XML and this document
  reconciled; in-game playtest pending.
- v1.3 (2026-10-27) Doriath Ranger ambush: the first ranged attack launched
  after an attack order received while concealed against an unaware target
  deals +50% damage. The one-shot bonus is consumed at launch and is canceled
  by movement, damage, or replacing the attack order before launch.
  Implemented with a Ranger-specific component and a narrowly scoped
  `Attack.PerformAttack` hook; in-game validation remains pending.

Future changes should increment this document's version and record the
reason, affected templates, and verification status in its short history.
Do not recreate parallel versioned numeric roster documents.

## Source-of-truth and data coverage

1. Simulation templates determine in-game values, including inheritance,
   attack bonuses, auras, class modifiers, and special attacks.
2. This document records the intended and reconciled values. Where it
   summarizes rather than repeats a value, the template path is included.
3. `unit_stats.csv` is not yet a complete effective-stat dump: it omits
   population cost, movement speed, many support/naval/siege templates, and
   some inherited or multi-stanza attacks. Its weapon/class parsing has also
   historically misclassified some units. Do not use it alone for final
   power comparisons.
4. The 2026-10-20 plan's “55 base templates / 339 stat changes” statement
   describes that pass, not the entire set of unit templates. The five unit
   folders contain 89 non-promotion base templates in total. The next audit
   must classify which are actually trainable, summoned, or support-only,
   then expand the effective-stat export to cover every trainable unit.
5. Unless explicitly noted, `_a` and `_e` promotion templates inherit their
   base unit's combat stats. Verify that assumption for each family when
   changing inheritance or promotion templates.

## Shared archetype anchors

These 0.28 archetypes are comparison references, not mandatory identical
stats. Weapon classes must be compared by damage per second, effective
damage against armour, range, role bonuses, training access, and replacement
cost—not by hit damage alone.

| Archetype | HP | Attack per hit | Hack/Pierce/Crush armour | Cost F/W/S/M | Train |
|---|---:|---|---|---|---:|
| Citizen melee infantry | 100 | 4.5 Hack + 4 Pierce | 3/3/15 | 50/50/0/0 | 10s |
| Citizen bow infantry | 50 | 7.2 Pierce | 1/1/10 | 50/20/0/0 | 10s |
| Citizen sling infantry | 50 | ~12 Pierce | 1/1/10 | 50/20/0/0 | 10s |
| Citizen javelin infantry | 50 | 16 Pierce | 1/1/10 | 50/20/0/0 | 10s |
| Melee cavalry | 160 | 6.6 Hack + 5.5 Pierce | 3/3/15 | 100/40/0/10 | 15s |
| Bow cavalry | 100 | 7.5 Pierce | 1/2/15 | 100/50/0/0 | 15s |
| Champion melee infantry | 200 | 14 Hack | 6/6/20 | 80/60/0/80 | 19s |
| Champion ranged infantry | 120 | 15 Pierce | 3/3/20 | 80/60/0/80 | 18s |
| Champion cavalry | 260 | 12 Hack + 10 Pierce | 6/5/20 | 150/80/0/100 | 25s |
| Melee hero | 1000 | 26 Hack | 12/12/25 | 200/150/0/200 | 50s |
| Ranged hero | 1000 | 27 Pierce | 6/6/25 | 200/200/0/150 | 50s |
| Cavalry hero | 1200 | 26 Hack | 9/11/25 | 300/150/0/300 | 50s |

### Shared conventions and rules

- Typical citizen melee cadence: 750ms swords/axes and 1000ms spears.
- Typical bows: 1250ms. Javelins: 1500ms. Deliberate exceptions are
  documented per unit.
- Heavy hold-line infantry may use 1000ms cadence as a conscious role trade.
- Armour order in balance tables is Hack/Pierce/Crush.
- Resource order is Food/Wood/Stone/Metal.
- Basic infantry intended to be available in Village Phase should not require
  Stone or Metal unless its role has a clear specialization (for example,
  Stone-fed slingers). Existing exceptions are recorded as review items;
  costs remain at the implemented baseline until the holistic power review.
- No basic unit should combine best-in-class health, armour, speed, damage,
  and cost. Elites require practical counters.
- Cost, training time, population, production building/phase access, and
  faction bonuses must be evaluated together.
- Promotion ranks should not receive hidden stat deltas unless the unit
  design explicitly calls for them.

### Spear damage convention

Spear unit lines use mixed Hack/Pierce damage while preserving their existing
base damage totals, plus the existing 2.5x anti-cavalry multiplier. Apply
these rounded splits to the implemented spear infantry and Númenórean scout
line; do not apply them to spear heroes or the Doriath Sindar Axeman.

| Existing total | Hack | Pierce |
|---:|---:|---:|
| 6 | 3.5 | 2.5 |
| 7 | 4 | 3 |
| 8 | 4.5 | 3.5 |
| 10 | 5.5 | 4.5 |

## Faction identity hypotheses

These are lore/design hypotheses, not a validated power ranking. The faction
ordering previously asserted by the rebalance plan is removed until a
holistic comparison has been run.

| Faction | Intended identity | Current balance hypothesis |
|---|---|---|
| Doriath | Hidden Sindar realm; prepared terrain, concealment, quality | High positional value, weaker open-field flexibility |
| Lindon | Noldorin craft, disciplined infantry, naval strength | High quality and coastal value, expensive replacement |
| Mordor | Horde, attrition, territorial pressure | Lower individual cost/quality, mass and economic pressure |
| Moria | Durable infantry, deep mining, tunnels, siege support | Strong defensive endurance, slow surface flexibility |
| Númenor | Peak Dúnedain infrastructure, disciplined quality | Strong core infantry and navy; light scout cavalry only |

## Implemented combat baseline

Values below reflect the reconciled implementation as of v1.1. `A` means
armour in Hack/Pierce/Crush order; costs are Food/Wood/Stone/Metal; time is
seconds. This table covers the core combat roster and includes template-derived
summaries for selected siege and special units, even where the current export
has no row. It is not a replacement for the complete effective-stat audit in
the continuation plan.

### Doriath

| Unit / template | Role / weapon | HP | Attack per hit / interval | Range | A | Cost | Time | Notes |
|---|---|---:|---|---:|---|---|---:|---|
| Green-weave Scout `infantry_scout` | Scout / bow | 60 | 5 Pierce / 1250ms | 32 | 1/1/10 | 35/10/0/0 | 10 | 4x vs Animal; +10% forest move |
| Doriath Hunter `infantry_hunter` | Stealth skirmisher / javelin | 60 | 16 Pierce / 1500ms | 45 | 1/1/10 | 45/20/0/0 | 10 | Forest camouflage; +10% forest move |
| Sindar Axeman `infantry_spearman` | Basic melee / axe | 110 | 7 Hack / 1000ms | — | 3/3/15 | 45/40/0/5 | 12 | No anti-cavalry bonus |
| Doriath Ranger `infantry_ranger` | Ambush archer / bow | 85 | 8 Pierce / 1250ms | 65 | 2/2/10 | 50/30/0/5 | 12 | Forest camouflage; +10% forest move |
| Doriath Guardian `infantry_guardian` | Hold-line / dual axes | 155 | 9 Hack / 1000ms | — | 3/3/13 | 60/40/0/15 | 14 | Forest armour +2/+2/+2 (5/5/15 in forest); visual animation follow-up required |
| Doriath Sentinel `infantry_sentinel` | Long-range support / bow | 115 | 10 Pierce / 2000ms | 75 | 2/4/10 | 60/40/0/10 | 16 | Long-range cadence exception |
| March-warden `champion_marchwarden` | Champion / stealth bow | 205 | 16 Pierce / 1250ms | 70 | 6/6/20 | 80/60/0/80 | 20 | Forest camouflage; +10% forest move; nearby enemy vision aura |
| Doriath Saboteur `infantry_saboteur` | Demolition | 100 | 5 Hack / 2500ms | 4 | 2/2/15 | 70/40/0/20 | 20 | 10x vs structures; restricted vs units |
| Thingol `hero_thingol` | Hero / melee | 1000 | 22 Hack / 1000ms | — | 12/12/25 | 200/150/0/200 | 50 | Command aura |
| Beleg `hero_beleg` | Hero / bow | 1000 | 27 Pierce / 1500ms | 78 | 6/6/25 | 200/200/0/150 | 50 | Guidance aura |
| Melian `hero_melian` | Hero / healer | 900 | — | — | 12/12/25 | 250/0/100/150 | 50 | Girdle aura and healing |

### Lindon

| Unit / template | Role / weapon | HP | Attack per hit / interval | Range | A | Cost | Time | Notes |
|---|---|---:|---|---:|---|---|---:|---|
| Lindon Recruit `infantry_recruit` | Basic melee / sword | 105 | 7 Hack / 750ms | — | 3/3/15 | 40/35/0/0 | 10 | |
| Lindon Spearman `infantry_spearman` | Spear infantry | 120 | 4 Hack + 3 Pierce / 1000ms | — | 3/3/15 | 45/40/0/5 | 12 | 2.5x vs Cavalry |
| Lindon Archer `infantry_archer` | Archer / bow | 70 | 8 Pierce / 1250ms | 60 | 1/2/10 | 45/25/0/5 | 10 | |
| Lindon Guard `infantry_guard` | Phalanx / spear | 175 | 5.5 Hack + 4.5 Pierce / 1000ms | — | 5/5/15 | 60/40/0/15 | 14 | 2.5x vs Cavalry |
| Lindon Mariner `infantry_mariner` | Coastal infantry / sword | 115 | 8 Hack / 750ms | — | 3/3/15 | 50/40/0/5 | 12 | Dock/Swan Ship aura |
| Lindon Champion `champion_infantry` | Champion / sword | 210 | 14 Hack / 750ms | — | 7/7/20 | 80/60/0/80 | 20 | Morale aura |
| Mithlond Border Rider `cavalry_border_rider` | Light cavalry / bow | 100 | 7.5 Pierce / 1100ms | 55 | 2/1/15 | 100/50/0/0 | 15 | |
| Círdan `hero_cirdan` | Hero / melee | 1000 | 26 Hack / 750ms | — | 12/12/25 | 200/200/0/200 | 50 | Naval auras |
| Elrond `hero_elrond` | Hero / melee | 1000 | 26 Hack / 750ms | — | 12/12/25 | 200/150/0/250 | 50 | Vilya's Rest |
| Gil-galad `hero_gil_galad` | Hero / spear | 1100 | 26 Hack + 14 Pierce / 1000ms | — | 12/12/25 | 250/200/0/300 | 50 | Spear bonus and aura |
| Vanguard Saboteur `infantry_saboteur` | Structure demolition | 130 | 2 Hack + 30 Crush / 2500ms | 4 | 3/3/15 | 90/40/0/40 | 25 | Cannot attack units |

### Mordor

| Unit / template | Role / weapon | HP | Attack per hit / interval | Range | A | Cost | Time | Notes |
|---|---|---:|---|---:|---|---|---:|---|
| Orc Warrior `infantry_warrior` | Basic melee / sword | 90 | 6 Hack / 750ms | — | 2/2/10 | 30/10/0/0 | 10 | |
| Orc Spearman `infantry_spearman` | Spear infantry | 100 | 3.5 Hack + 2.5 Pierce / 1000ms | — | 2/2/10 | 35/15/0/0 | 10 | 2.5x vs Cavalry |
| Orc Archer `infantry_archer` | Archer / bow | 60 | 6 Pierce / 1250ms | 55 | 1/1/10 | 35/15/0/5 | 10 | |
| Variag Rider `cavalry_variag_rider` | Light cavalry / bow (hired) | 110 | 7 Pierce / 1200ms | 50 | 1/2/15 | 90/50/0/10 | 15 | Mordor's only cavalry; CC-trained citizen-cavalry, no stable |
| Black Uruk `champion_uruk` | Champion / sword | 180 | 12 Hack / 750ms | — | 5/5/15 | 70/30/0/60 | 24 | |
| Olog-hai `champion_olog_hai` | Champion troll / boulder and melee | 500 | 22 Crush / 3200ms ranged; 24 Hack + 24 Crush / 2000ms melee | 70 ranged | 8/8/20 | 200/60/0/80 | 30 | Morgul Dread aura slows enemy attack; ranged splash also applies |
| Mountain Troll `infantry_troll` | Siege support / boulder and melee | 360 | 18 Crush / 3500ms ranged; 20 Hack + 18 Crush / 2200ms melee | 65 ranged | 6/4/15 | 160/80/0/10 | 20 | Breeding Pits; metal-cheap bred beast; ranged splash also applies |
| Crebain `scout_crebain` | Flying scout | 120 | No normal attack | — | 30/0/30 | 30/20/0/0 | 10 | Concealed-unit detection |
| Sauron `hero_sauron` | Hero / crush | 1500 | 26 Hack + 30 Crush / 2200ms | — | 15/15/30 | 400/0/0/600 | 60 | Boss exception; strong Morgul Dread aura |
| Gothmog `hero_gothmog` | Hero / melee | 1000 | 26 Hack / 750ms | — | 12/12/25 | 250/0/0/250 | 50 | Fury + strong Morgul Dread auras |
| Khamûl `hero_khamul` | Hero cavalry / melee | 1200 | 26 Hack / 1000ms | — | 11/9/25 | 300/0/0/300 | 50 | Hunt + strong Morgul Dread auras |
| Siege Catapult `siege_catapult` | Siege | 220 | 75 Crush / 5000ms | 180 | 2/5/8 | 0/100/0/100 | 25 | Area attack |
| Grond `siege_grond` | Siege | 260 | 90 Crush / 5000ms | 6.5 | 2/6/8 | 0/120/0/120 | 35 | Structure-only breacher |

### Moria

| Unit / template | Role / weapon | HP | Attack per hit / interval | Range | A | Cost | Time | Notes |
|---|---|---:|---|---:|---|---|---:|---|
| Tunnel Runner `infantry_runner` | Mobile melee / sword | 100 | 6 Hack / 750ms | — | 2/2/10 | 40/25/0/5 | 10 | |
| Moria Spearman `infantry_spearman` | Spear infantry | 130 | 4 Hack + 3 Pierce / 1000ms | — | 4/3/15 | 45/35/0/10 | 12 | 2.5x vs Cavalry |
| Moria Battle Dwarf `infantry_dwarf` | Melee / sword | 140 | 8 Hack / 750ms | — | 4/3/15 | 50/30/0/15 | 12 | |
| Moria Guardsman `infantry_guardsman` | Hold-line / sword | 140 | 8 Hack / 750ms | — | 4/4/15 | 50/30/0/20 | 14 | |
| Moria Axe-Thrower `infantry_archer` | Short-range skirmisher / throwing axe | 75 | 10 Hack + 4 Pierce / 1500ms | 40 | 1/2/10 | 45/25/0/5 | 12 | |
| Mountain Ranger `infantry_ranger` | Scout / throwing axe | 95 | 10 Hack + 4 Pierce / 1500ms | 40 | 2/2/10 | 50/30/0/10 | 14 | 3x vs Animal |
| Moria Breaker `infantry_breaker` | Bruiser / sword | 190 | 11 Hack + 15 Crush / 1000ms | — | 6/5/15 | 70/30/0/40 | 15 | |
| Mithril Vanguard `champion_vanguard` | Champion / sword | 235 | 13 Hack + 8 Crush / 750ms | — | 7/6/20 | 80/40/50/80 | 24 | |
| Fundin `hero_fundin` | Hero / melee | 900 | 20 Hack / 1800ms | — | 10/10/25 | 180/50/0/150 | 50 | Providence aura |
| Náin `hero_nain` | Hero / melee and crush | 1000 | 22 Hack + 12 Crush / 1700ms | — | 12/12/25 | 200/0/50/200 | 50 | Wrath aura |
| Durin VI `hero_durin` | Hero / melee and crush | 1100 | 20 Hack + 10 Crush / 1700ms | — | 12/12/25 | 200/0/100/200 | 50 | Endurance aura |
| Siege Engineer `siege_engineer` | Siege infantry | 180 | 4 Hack + 65 Crush / 4500ms | — | 2/4/7 | 0/100/0/70 | 20 | Population 2; repairs engines |
| Steam Ram `siege_ram` | Siege | 320 | 80 Crush / 4000ms | 6.5 | 2/50/8 | 0/120/0/80 | 25 | Population 3; structure-only |

### Númenor

| Unit / template | Role / weapon | HP | Attack per hit / interval | Range | A | Cost | Time | Notes |
|---|---|---:|---|---:|---|---|---:|---|
| Númenórean Recruit `infantry_recruit` | Basic melee / sword | 105 | 7 Hack / 750ms | — | 3/3/15 | 45/40/0/5 | 10 | |
| Númenórean Spearman `infantry_spearman` | Spear infantry | 119 | 4 Hack + 3 Pierce / 1000ms | — | 3/3/15 | 50/40/0/5 | 12 | 2.5x vs Cavalry |
| Númenórean Archer `infantry_archer` | Archer / bow | 69 | 8 Pierce / 1250ms | 60 | 1/2/10 | 50/25/0/5 | 10 | |
| Great Coast Guard `infantry_coast_guard` | Coastal infantry / sword | 114 | 8 Hack / 750ms | — | 3/3/15 | 55/40/0/10 | 12 | |
| Númenórean Guard `infantry_guard` | Hold-line / sword | 167 | 10 Hack / 1000ms | — | 5/5/15 | 65/40/0/15 | 14 | |
| Númenórean Scout `cavalry_scout` | Scout cavalry / spear | 110 | 4.5 Hack + 3.5 Pierce / 1000ms | — | 3/2/15 | 80/40/0/5 | 15 | 2.5x vs Cavalry |
| Númenórean Champion `champion_infantry` | Champion / sword | 210 | 14 Hack / 750ms | — | 7/7/20 | 85/60/0/80 | 20 | |
| Númenórean Royal Guard `infantry_guard_king` | Champion / sword | 220 | 14 Hack / 750ms | — | 7/7/20 | 90/60/0/90 | 22 | |
| Steel-bow Archer `champion_archer` | Champion / bow | 140 | 15 Pierce / 1250ms | 78 | 3/3/20 | 80/60/0/80 | 18 | Cadence aligned to v1.0 bow rule |
| Isildur `hero_isildur` | Hero / melee | 1000 | 24 Hack / 1500ms | — | 11/11/25 | 200/100/0/200 | 50 | Valour aura |
| Ar-Pharazôn `hero_pharazon` | Hero / melee | 1050 | 24 Hack / 1500ms | — | 12/12/25 | 250/150/0/300 | 50 | Sea-Kings' Command; Great Armament |
| Elendil `hero_elendil` | Hero / melee | 1100 | 26 Hack / 1500ms | — | 12/12/25 | 200/150/0/250 | 50 | Command aura |

### Other base templates and coverage

The following non-promotion templates are present in the five unit folders
but do not yet have complete effective-stat rows in `unit_stats.csv`.
Some, such as the Mordor siege units above, have manual summaries here;
template inheritance and trainer references still need auditing.

| Faction | Additional template IDs | Known direct combat/economy values |
|---|---|---|
| Doriath | `ship_fishing`, `siege_ent`, `support_healer`, `support_trader`, `support_worker` | Ent: 420 HP, 40 Crush / 4500ms at range 80 (2x vs structures); melee 12 Hack + 10 Crush / 2500ms; cost 100/100/0/50, population 3. Worker: 65 HP, 50 Food. |
| Lindon | `ship_fire_galley`, `ship_fishing`, `ship_merchant`, `siege_bolt_thrower`, `support_healer`, `support_trader`, `support_worker`, `swan_ship` | Bolt-Thrower: 180 HP, 50 Pierce / 5000ms at range 165; cost 0/120/0/120, population 2. Swan Ship: 800 HP, 20 capacity, cost 0/150/0/80, population 2. |
| Mordor | `support_trader`, `support_worker`; `siege_catapult` and `siege_grond` are summarized above but absent from the CSV; `eye_seer` is spawned by the Eye | Snaga: 55 HP, 2 Hack / 2000ms; cost 35 Food. |
| Moria | `siege_engineer`, `siege_ram`, `support_provisions_cart`, `support_trader`, `support_worker` | Siege Engineer: 180 HP, 4 Hack + 65 Crush / 4500ms; cost 0/100/0/70, population 2. Steam Ram: 320 HP, 80 Crush / 4000ms; cost 0/120/0/80, population 3. Provisions Cart: 150 HP, cost 60/40/0/0. Laborer: 75 HP, 50 Food. |
| Númenor | `fishing_boat`, `ship_juggernaut`, `ship_siege`, `ship_warship`, `siege_ballista`, `support_healer`, `support_trader`, `support_worker`, `trading_ship` | Steel-Bow Ballista: 220 HP, 60 Pierce / 5000ms at range 185; cost 0/150/0/150, population 3. Siege Ship: 1200 HP, 40 Pierce + 30 Crush / 6000ms at range 170; cost 0/250/0/250, population 3. |

Ship, trader, and healer rows above may inherit important values from their
vanilla parent templates. A full audit must resolve those values rather than
leave them as blanks. The Eye Seer is listed for completeness but is
script-spawned rather than trained.

## Agreed implementation updates in v1.0

- Doriath Hunter: bow changed to javelin; 16 Pierce, 1500ms, range 45.
- March-warden: melee champion changed to stealth-bow champion; 16 Pierce,
  1250ms, range 70, forest camouflage, and existing enemy-vision aura kept.
- Doriath Spearman role renamed Sindar Axeman; 7 Hack, no anti-cavalry
  bonus. Guard of the Caves visuals use dual axes rather than sword/shield.
- Lindon Guard converted to Noldorin Phalanx spear role; 10 total base damage
  split 5.5 Hack + 4.5 Pierce and 2.5x vs Cavalry.
- Moria Archer and Mountain Ranger converted to short-range throwing axes:
  10 Hack + 4 Pierce, 1500ms, range 40. Ranger retains 3x vs Animal.
- Númenórean Scout converted to spear; 8 total base damage split 4.5 Hack +
  3.5 Pierce and 2.5x vs Cavalry.
- Spear infantry mixed-damage splits follow the table above. Spear heroes
  retain their existing attack profiles.
- Númenor Steel-bow Archer cadence changed from 2500ms to 1250ms.

These changes keep each unit's other rebalance values unchanged unless
specified above. Reassess all profiles in the forthcoming holistic power
comparison before treating them as final balance.

## Implemented mechanics and known mismatches

- **Doriath Girdle:** retain the structure-projected movement/vision effects.
  It should be stronger around its structures; do not require forest-density
  scaling or weaken it in open ground. Doriath still needs to clear trees for
  Wood. Exact aura values and coverage belong to the structure/aura templates.
- **Doriath forest bonuses:** stationary forest camouflage is implemented
  for selected units. The forest movement bonus (Green-weave Scout, Doriath
  Hunter, Doriath Ranger, March-warden: +10% in forest) and the forest-only
  Guardian armour bonus (base 3/3/13, +2 Hack/Pierce/Crush in forest) are now
  live through the `ForestAffinity` component, which toggles self-applied
  modifiers from tree density. An attack order against a target that has not
  detected the concealed Ranger arms its one-shot +50% ranged-damage ambush
  bonus, consumed when the attack launches.
- **Doriath dual-axe visuals:** Guard of the Caves must carry two axes and no
  shield. Current actors replace the weapon and shield props; the attack/idle
  animation is still reused from a sword-and-shield actor and needs a proper
  dual-wield art/animation pass.
- **Lindon Noldorin Metallurgy:** implementation adds +1 Pierce attack damage
  to Champions, not Pierce armour. Correct references to the effect.
- **Morgul Dread:** carried by the Olog-hai (radius 25, ~13% slower enemy
  attacks) and, stronger, by the Mordor heroes (radius 35, ~23% slower);
  armour reduction is intentionally excluded so the fear effect stays focused
  on attack cadence instead of compounding with extra damage vulnerability.
- **Khamûl:** the implemented aura boosts movement and melee Hack for nearby
  Orc-class units. Additional enemy fear and bonuses against
  workers/isolated targets from earlier faction notes are intentionally
  excluded.
- **Moria Mithril Core:** depletion conversion to a permanent 50%-yield
  metal shaft is implemented. Worker-presence/upkeep requirements remain
  deferred. The separate Mithril Deep-Shaft structure also has a metal
  trickle, and Deep Delving adds +15% stone/metal gathering.
- **Moria tunnels:** current effects are +7% movement near tunnel mouths and
  a separate global +5% infantry movement technology. Restricting the bonus
  to linked tunnels only remains deferred.
- **Lindon Swan Ship:** current Phase II ship has 20 infantry capacity and can
  train eligible infantry aboard at full cost without requiring undamaged
  status or proximity to friendly structures. An additional per-ship lifetime
  cap or training cooldown is intentionally excluded; normal resource/population
  costs and the standard training queue apply. Verify shoreline
  disembarkation in-game.
- **Númenor:** Scout cavalry is light scouting/anti-cavalry only; this is not
  a claim that Númenor fields strong shock or champion cavalry. House
  population and infantry health bonuses are implemented at +10% and +5%.
  Ar-Pharazôn's finalized design also includes +10% Metal cost for Númenórean
  land units and +10% maximum population while he lives, multiplicative with
  other population-cap bonuses; no land-training slowdown. These two effects
  are implemented via the Great Armament aura.
- **Village-phase costs:** current templates do not consistently meet the
  design rule that ordinary Village-phase basic units avoid Stone/Metal
  unless specialized. Retain current costs for v1.0; audit this during the
  holistic comparison.

## Complete-inventory continuation plan

The unit-stat table above covers the combat rows currently represented in
the export, not every base template. Close that coverage gap before claiming
an all-faction power comparison is complete:

1. Inventory all non-promotion templates by actual trainer/building and tag
   each as trainable, summoned, support, civilian, naval, or siege. The five
   unit directories contain 89 non-promotion base templates; this count is
   not itself a count of trainable units.
2. Add missing workers, traders, healers, ships, siege engines, the Doriath
   Ent, and other support/special units to a complete effective-stat export.
   Include HP, all attack stanzas and bonuses, armour, cost, time, population,
   speed, range, phase, training building, and relevant auras/technologies.
3. Resolve vanilla inheritance and faction tech/auras instead of treating
   child XML overrides as the complete effective unit.
4. Correct CSV class/weapon parsing; specifically validate cavalry classes,
   the Olog-hai, multi-attack units, and units with special parent classes.
5. Cross-check all rows against template IDs and the in-game tooltip or
   debug-stat output; do not infer effective stats from rank CSV rows.

## Holistic faction-power comparison plan

After the complete inventory exists, compare equivalent roles with faction
bonuses first disabled, then enabled. Use matched population, resource
investment, production access, and replacement time; include counters and
the terrain/strategic context relevant to each faction.

Required tests:

- Equal-role basic-unit and elite/counter engagements, including damage type
  against relevant armour and mixed attack stanzas.
- Equal-population and equal-resource-budget comparisons, with training
  throughput and production access included.
- Economy snapshots at 20 and 35 minutes.
- Open terrain, forest, mountain/chokepoint, and coastal maps.
- Heroes, wonders, technologies, and faction auras disabled first, then
  enabled in separate runs.
- Record scenario, map, seed, unit counts, population, resource spend,
  upgrades, duration, losses, and outcome. Do not declare a faction ordering
  without repeatable test evidence.

## Future versioning

Use v1.1 for the next implementation or measured-balance revision. Each
revision should summarize changed unit IDs and values, the reason, whether
the XML and this document agree, and what tests were run. Keep faction
identity references in the faction documents; do not duplicate the full
numeric baseline there.
