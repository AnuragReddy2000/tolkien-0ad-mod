# Rohan — Unit Balance v0.2

> **Active balance target:** This roster is synchronized with `docs/balance/v0.2-active-targets.md`. Use these values for implementation until a later balance revision supersedes them.

Costs are Food/Wood/Stone/Metal.

| Unit | Phase | Cost | Pop | HP | Speed | Attack / interval | Range | Armour H/P/C | Quirk |
|---|---|---:|---:|---:|---:|---|---:|---:|---|
| Rohan Villager | I | 50/0/0/0 | 1 | 70 | 1.0 | 2 hack / 2.0s | — | 0/0/0 | Standard worker |
| Rohan Scout | I | 55/0/0/20 | 1 | 105 | 1.35 | 5 hack / 1.6s | — | 0/1/0 | +25 sight; low combat value |
| Rohan Spearman | I | 35/10/0/10 | 1 | 105 | 1.0 | 6 hack / 1.6s; +8 vs cavalry | — | 1/1/0 | Brace and anti-charge |
| Rohan Rider | II | 70/0/0/45 | 1 | 145 | 1.3 | 8 hack / 1.7s; charge 14 | — | 2/2/1 | High mobility; weak to braced spears |
| Rohan Archer | II | 40/25/0/10 | 1 | 70 | 1.05 | 6 pierce / 1.8s | 60 | 0/1/0 | Mobile ranged support |
| Rohirrim | II | 75/0/0/55 | 1 | 205 | 1.35 | 11 hack / 1.8s; charge 20 | — | 3/3/2 | Charge cooldown 12s |
| Rohan Guard | III | 55/0/0/35 | 1 | 160 | 1.0 | 9 hack / 1.7s | — | 4/4/1 | Infantry anchor; slower than cavalry |
| Rohan Champion | III | 80/0/0/65 | 1 | 245 | 1.3 | 14 hack / 1.8s; charge 24 | — | 5/5/2 | Cavalry leadership aura |

## Balance quirks

- Pastures of the Mark: each active pasture produces 0.4 Food/second; maximum four pastures per Civic Center.
- Éored Wedge: **+10% charge damage and +5% movement before contact; -20% turn rate; charge bonus cannot repeat until 12s have elapsed.**
- Defensive Stakes deal 12 crush damage to cavalry crossing them and are vulnerable to infantry, fire, and siege. Their durability must remain low enough that siege and fire can clear them.
- Field Camps provide rallying and local reinforcement but do not train citizens or replace Civic Centers.
- Helm’s Horn is a short disruption effect, not a hard stun or fear lock.
