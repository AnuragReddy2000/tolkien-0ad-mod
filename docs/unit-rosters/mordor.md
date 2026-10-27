# Mordor Unit Roster

For current numeric profiles, shared balance rules, and implementation status,
see the [canonical unit-balance specification](../balance/unit-balance.md).
This page records roles only; it is not a second balance target.

| Unit | Template | Role |
|---|---|---|
| Snaga Slave | `support_worker` | Civilian worker |
| Snaga Caravan | `support_trader` | Trader |
| Orc Warrior | `infantry_warrior` | Cheap basic melee infantry |
| Orc Spearman | `infantry_spearman` | Mass anti-cavalry infantry |
| Orc Archer | `infantry_archer` | Cheap ranged pressure |
| Variag Rider | `cavalry_variag_rider` | Hired Khand horse archer; Mordor's only cavalry (Civic Centre) |
| Crebain | `scout_crebain` | Fast flying reconnaissance; no attack; Doriath camouflage hides from it until broken |
| Black Uruk | `champion_uruk` | City-phase elite infantry |
| Mountain Troll | `infantry_troll` | Metal-cheap bred beast; dual-mode boulder and melee siege support (Breeding Pits) |
| Olog-hai | `champion_olog_hai` | Champion troll; dread slows enemy attack cadence |
| Siege Catapult | `siege_catapult` | Area siege |
| Grond | `siege_grond` | Structure-only champion ram |
| Sauron, Gothmog, Khamûl | `hero_*` | Distinct late-game hero roles |

Morgul Dread is carried by the Olog-hai and, stronger, by the Mordor heroes;
it slows enemy attack cadence. Armour reduction from earlier design notes is
not part of the current design, keeping the aura focused on fear rather than
stacking a second combat debuff. The Eye Seer is spawned by Barad-dûr and is
not a normal trainable unit.
