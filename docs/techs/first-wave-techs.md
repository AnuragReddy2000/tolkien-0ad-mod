# First-Wave Technology Reference

Technology reference for the five first-wave factions (Lindon, Doriath,
Mordor, Moria, Númenor). The tables record planned and existing effects;
technology JSON and simulation templates are authoritative for what is
currently implemented. Each faction's design target is one economic tech,
one infantry/ranged tech, one faction-identity tech, one Town-to-City tech,
and one late-game tech.

## Conventions

- Tech tokens are flat paths under `simulation/data/technologies/` (vanilla A28 layout —
  no per-building subfolders). File name = tech token.
- Phase gating uses the `phase_town` / `phase_city` tokens. The faction Civic Centres
  research `phase_town_{civ}` / `phase_city_{civ}`, which fall back to
  `phase_town_generic` / `phase_city_generic`; those `replaces`/`supersedes` the plain
  tokens, so `requirements: { "tech": "phase_town" }` resolves correctly (same pattern as
  the existing `lindon_noldorin_metallurgy`).
- The Civic Centre's two phase techs are the faction's **Town-to-City** slot for §11
  purposes (they are the phase-gated research decisions that gate City content).
- Stat modifiers use vanilla component paths only (`Health/Max`, `Attack/*/Damage/*`,
  `Vision/Range`, `UnitMotion/WalkSpeed`, `ResourceGatherer/Rates/*`,
  `Cost/BuildTime`, `Cost/Resources/*`). Doriath's `doriath_guardianship_of_the_greenwood`
  is a scripted gathering rule keyed to a researched technology; stealth, Girdle
  deepening, and tunnel effects remain separate prototypes (plan §9).
- Icons are vanilla `art/textures/ui/session/portraits/technologies/` names (verified
  present in the installed A28 `public.zip`).
- Costs/times mirror vanilla stat-tech bands: Town ~150–200 / 40–60 s, City ~200–400 /
  60 s.
- Stacking rule for every tech below: single research, no supersedes chain, modifiers
  apply once. No tech grants an undocumented global statistic (§11).

## Lindon

| Slot | Token | Building | Phase | Cost | Time | Affects | Effect | Counterplay |
|---|---|---|---|---|---|---|---|---|
| Economic | `lindon_harvest_of_the_falas` | Dock | Town | 150 wood | 45 s | FishingShip | +25% fish gather rate | Deny coastal access (docs/factions/lindon.md) |
| Infantry/ranged | `lindon_noldorin_metallurgy` | Forge | Town | 200 food 300 metal | 45 s | Champion | +1 Pierce attack damage (implemented) | Cheap mass trades blows before City |
| Identity | `lindon_elven_ladders` | Fortress | City | 200 stone 200 metal | 60 s | Fortress, StoneTower | +15% health | Siege; Lindon must reach City and pay |
| Town-to-City | `phase_town_lindon` → `phase_city_lindon` | Civic Centre | II / III | vanilla | vanilla | — | Phase progression | Standard phase pressure |
| Late-game | `lindon_mithril_plated_hulls` | Dock | City | 200 metal 100 wood | 60 s | Ship | +15% ship health | Fireships, focus fire, enemy navy |
| Extra (siege) | `lindon_singing_arrows` | Forge | City | 200 wood 200 metal | 60 s | Siege, Saboteur | Bolt-Throwers +20% pierce, Saboteurs +25% crush | Kill the engines/saboteurs before City |
| Extra (economic) | `lindon_elven_planning` | Civic Centre | Town | 100 wood | 30 s | House | −25% house build time | Early pressure before expansion |

## Doriath

| Slot | Token | Building | Phase | Cost | Time | Affects | Effect | Counterplay |
|---|---|---|---|---|---|---|---|---|
| Economic | `doriath_wardens_glade` | Farmstead | Town | 150 food 100 wood | 45 s | Worker | +15% food and wood gather rate | Raid farms/woodlines; Doriath fields no cavalry |
| Infantry/ranged | `doriath_sindar_forging` | Forge | Town | 200 food 200 metal | 45 s | Infantry, Champion | +1 Hack attack | Ranged and cavalry punish weak melee |
| Identity | `doriath_girdle_of_melian` | Menegroth | City | 300 stone 100 metal | 60 s | Menegroth, Girdle | +33% Menegroth health, +25% vision; Menegroth projects the stronger Girdle while standing | Raze Menegroth; effect is structure-projected, not forest-density-scaled |
| Town-to-City | `phase_town_doriath` → `phase_city_doriath` | Civic Centre | II / III | vanilla | vanilla | — | Phase progression | Standard phase pressure |
| Late-game | `doriath_song_of_things_unseen` | Fortress | City | 300 stone 200 metal | 60 s | Structure | +15% building health | Siege and sustained pressure |
| Extra (identity) | `doriath_green_weave` | Barracks | Town | 100 wood 100 metal | 40 s | Scout | +15% scout vision | Enemy scout superiority, detection |
| Extra (economic) | `doriath_march_wardens` | Civic Centre | Town | 100 wood | 30 s | House | −25% house build time | Early pressure before expansion |
| Extra (identity) | `doriath_guardianship_of_the_greenwood` | Storehouse | Town | 150 food 100 wood | 45 s | Doriath gatherers | Leave at least 5% of each tree's maximum wood supply | Other factions can still exhaust the tree |

## Mordor

| Slot | Token | Building | Phase | Cost | Time | Affects | Effect | Counterplay |
|---|---|---|---|---|---|---|---|---|
| Economic | `mordor_orc_cookhouses` | Civic Centre | Town | 150 food | 45 s | Worker | +20% food gather rate | Snaga are the only gatherers — harass them |
| Infantry/ranged | `mordor_war_drums_of_angband` | Breeding Pits (barracks) | Town | 100 food 150 metal | 45 s | Orc | +1 Hack attack | Quality factions win clean battles |
| Identity | `mordor_black_uruk_forging` | Forge | Town | 200 food 300 metal | 45 s | Orc Champion | +15% health | Focus fire; elites are few |
| Town-to-City | `phase_town_mordor` → `phase_city_mordor` | Civic Centre | II / III | vanilla | vanilla | — | Phase progression | Standard phase pressure |
| Late-game | `mordor_engines_of_morgoth` | Workshop | City | 300 wood 200 metal | 60 s | Siege | +15% siege attack | Static defense, target the slow engines |

## Moria

| Slot | Token | Building | Phase | Cost | Time | Affects | Effect | Counterplay |
|---|---|---|---|---|---|---|---|---|
| Economic | `moria_deep_delving` | Civic Centre | Town | 150 wood 150 metal | 45 s | Worker | +15% stone and metal gather rate | Slow expansion; raid the mining line |
| Infantry/ranged | `moria_dwarven_axe_mastery` | Forge | Town | 200 food 200 metal | 45 s | Infantry | +1 Hack attack | Ranged kiting; cavalry |
| Identity | `moria_khazad_forging` | Fortress | City | 300 stone 200 metal | 60 s | Structure | +15% building health | Siege attrition elsewhere while walls hold |
| Town-to-City | `phase_town_moria` → `phase_city_moria` | Civic Centre | II / III | vanilla | vanilla | — | Phase progression | Standard phase pressure |
| Late-game | `moria_deep_roadways` | Fortress | City | 200 wood 200 metal | 60 s | Infantry | +5% movement speed | Force Moria into open battle (docs/factions/moria.md) |
| Extra (economic) | `moria_stone_halls` | Civic Centre | Town | 100 stone | 30 s | House | −25% house build time | Early pressure before expansion |
| Food-for-trade (replaces farm upgrades) | `moria_pacts_with_dale` | Market | Town | 150 wood 150 metal | 40 s | Trader | +15% trade gain (take it in food) | Raid caravans; no trade, no bonus |
| Food-for-trade (replaces farm upgrades) | `moria_deep_larders` | Market | City | 200 wood 250 metal | 60 s | Player | +1.0 food trickle per second | Standard pressure; trickle alone won't feed an army |

> Moria Provision Hall researches no `gather_farming_*` grain techs by design (Dwarves
> abandoned farming for mining and trade); it keeps `gather_wicker_baskets` (wild
> foraging). Base fields stay for the early game; the two Market techs above cover the
> ~20% grain-rate gap instead. All Moria techs carry a `{"civ": "moria"}`
> requirement (vanilla civ-specific pattern): no-op for Moria research, blocks
> cross-civ research from captured buildings, and makes the civ overview list
> them under Specific Technologies.

## Númenor

| Slot | Token | Building | Phase | Cost | Time | Affects | Effect | Counterplay |
|---|---|---|---|---|---|---|---|---|
| Economic | `numenor_shipwrights_of_the_royal_harbour` | Dock | Town | 150 wood | 45 s | FishingShip | +25% fish gather rate | Deny the coast |
| Infantry/ranged | `numenor_dunedain_tempering` | Forge | Town | 200 food 300 metal | 45 s | Infantry, Champion | +1 Hack attack | Attrition and mass (Númenor is expensive) |
| Identity | `numenor_citadel_of_armenelos` | Fortress | City | 300 stone 200 metal | 60 s | Fortress | +15% health | Siege; Númenor must reach City |
| Town-to-City | `phase_town_numenor` → `phase_city_numenor` | Civic Centre | II / III | vanilla | vanilla | — | Phase progression | Standard phase pressure |
| Late-game | `numenor_fleet_of_the_lords_of_the_sea` | Dock | City | 300 metal 150 wood | 60 s | Warship | +15% warship attack | Fireships, massed anti-ship defense |
| Extra (economic) | `numenor_kings_building_craft` | Civic Centre | Town | 100 wood | 30 s | House | −25% house build time | Early pressure before expansion |

## Deliberately deferred (not stat techs)

- Doriath Forest Camouflage uses its unit/structure components. The Girdle is
  structure-projected; do not substitute a global stat bonus or forest-density condition.
- Moria Mithril Core (Deep Shafts) and tunnel capture behavior — structure/script work,
  not a tech.
- Númenor geography bonus — conditional terrain effect, §9-class prototype.
- Lindon Swan Ship lifetime limit and cooldown remain undecided; eligible
  infantry can train aboard at full cost without damage or friendly-structure
  proximity restrictions. Verify shoreline disembarkation in-game.

## Balance process

Treat technology values above as a reference, not a separate balance version.
After the five-faction baseline, record measured unit changes in
`docs/balance/unit-balance.md` as v1.1 or later. Keep this table synchronized
with implemented technology JSON; never treat a planned effect as live without
verifying its implementation.