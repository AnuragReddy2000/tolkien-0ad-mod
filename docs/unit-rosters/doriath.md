# Doriath Unit Roster

For current numeric profiles, shared balance rules, and implementation status,
see the [canonical unit-balance specification](../balance/unit-balance.md).
This page records roles only; it is not a second balance target.

| Unit | Template | Role |
|---|---|---|
| Doriath Gatherer | `support_worker` | Civilian worker |
| Green-weave Scout | `infantry_scout` | Fast foot scout; forest camouflage and bonus against animals |
| Doriath Hunter / Laiquendi Skirmisher | `infantry_hunter` | Stealth javelin skirmisher |
| Sindar Axeman | `infantry_spearman` | Basic melee infantry; no cavalry-counter bonus |
| Doriath Ranger | `infantry_ranger` | Forest-camouflaged archer |
| Guard of the Caves | `infantry_guardian` | Durable hold-line fighter; dual axes, no shield |
| Doriath Sentinel | `infantry_sentinel` | Long-range archer support |
| March-warden | `champion_marchwarden` | Forest-camouflaged bow champion; retains enemy-vision aura |
| Doriath Saboteur | `infantry_saboteur` | Structure demolition; cannot attack units |
| Ent-ally | `siege_ent` | Rare organic siege and melee support |

Doriath has no cavalry or mechanical siege. The Hunter's Cache and other
proposed designs are not part of the military-unit roster. The Hunter's Cache
is an implemented food-only dropsite structure (`structures/doriath/hunters_cache`):
50 Wood, 10 Stone, 20-second build time. It supports forward foraging but does
not replace cavalry's military mobility, pursuit, or rapid-response roles.

## Implemented and deferred balance mechanics

- Forest movement (Scout, Hunter, Ranger, March-warden +10% in forest) and the
  Guard of the Caves' forest-only armour (base 3/3/13, +2 Hack/Pierce/Crush in
  forest) are implemented through the `ForestAffinity` component.
- A Ranger's first ranged attack launched after receiving an attack order
  while concealed and targeting an enemy that has not detected it deals +50%
  damage. The one-shot bonus is consumed at launch, even if a projectile
  misses; moving, taking damage, or replacing the attack order before launch
  cancels it.
- The Girdle remains a structure-projected movement/vision effect; it does not
  scale with forest density or become weaker on open ground.
- Guard of the Caves actors have the agreed dual-axe props, but still reuse
  sword-and-shield-derived animations. A dedicated dual-wield animation pass
  remains art follow-up.
