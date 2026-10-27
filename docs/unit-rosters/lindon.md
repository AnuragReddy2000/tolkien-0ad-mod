# Lindon Unit Roster

For current numeric profiles, shared balance rules, and implementation status,
see the [canonical unit-balance specification](../balance/unit-balance.md).
This page records roles only; it is not a second balance target.

| Unit | Template | Role |
|---|---|---|
| Lindon Worker | `support_worker` | Civilian worker |
| Spearmaiden | `infantry_spearman` | Basic spear infantry |
| Lindon Recruit | `infantry_recruit` | Basic sword infantry |
| Lindon Archer | `infantry_archer` | Standard ranged infantry |
| Noldorin Phalanx / Lindon Guard | `infantry_guard` | Elite spear infantry; anti-cavalry |
| Lindon Mariner | `infantry_mariner` | Coastal melee infantry |
| Lindon Champion | `champion_infantry` | Elite sword infantry |
| Mithlond Border Rider | `cavalry_border_rider` | Light cavalry skirmisher; not shock cavalry |
| Swan Ship | `swan_ship` | Transport and full-cost infantry reinforcement |
| Fire Galley, Fishing Boat, Merchant Ship | `ship_*` | Naval combat, fishing, and trade |
| Elven Bolt-Thrower | `siege_bolt_thrower` | Precision anti-siege engine |
| Vanguard Saboteur | `infantry_saboteur` | Fortress-trained structure demolition |

Lindon fields light border cavalry only, not champion or shock cavalry.
Swan Ships have capacity for 20 infantry and can train eligible infantry
aboard at full cost, including while damaged or away from friendly structures.
There is no additional per-ship lifetime training limit or cooldown; normal
resource/population costs and the standard training queue apply. Verify
shoreline disembarkation in-game.

Noldorin Metallurgy currently grants Champions +1 Pierce attack damage; it
does not grant Pierce armour. Refer to the canonical specification for the
effect's implementation status and the measured-balance continuation plan.
