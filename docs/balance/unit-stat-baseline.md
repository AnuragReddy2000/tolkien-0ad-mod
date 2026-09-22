# Unit Balance Specification v0.1

This is the first numeric balance pass for the six-faction vertical slice. Values are implementation targets, not immutable final values. They are deliberately expressed against a shared baseline so cross-faction comparisons remain possible.

## Baseline assumptions

- Standard citizen infantry: 100 HP, 5 hack, 1 pierce, 0 crush armour, 1.0 movement speed.
- Standard citizen archer: 60 HP, 6 pierce attack, 0.5 attack repeat, 50 range, 1.0 movement speed.
- Standard citizen cavalry: 120 HP, 7 hack attack, 1.25 movement speed.
- Costs are Food/Wood/Stone/Metal.
- `pop` is population cost.
- Attack values are base damage per attack before armour.
- Attack intervals are seconds.
- Armour is hack/pierce/crush.
- Ranges and speeds are targets for implementation in the selected 0 A.D. version.
- Heroes are excluded from normal unit-cost comparisons.

## Role targets

| Role | Typical HP | Main attack | Typical cost | Intended answer |
|---|---:|---:|---:|---|
| Basic infantry | 90–110 | 5–7 hack | 50–70 total | stronger infantry, ranged fire |
| Spearman | 100–125 | 5–7 hack, anti-cavalry bonus | 60–80 total | archers, flanking |
| Archer | 55–75 | 5–7 pierce | 60–80 total | cavalry, melee |
| Scout cavalry | 90–120 | 5–7 hack | 80–110 total | spears, towers |
| Elite infantry | 150–190 | 8–11 hack | 120–170 total | mass units, siege, ranged focus |
| Elite cavalry | 190–250 | 10–14 hack | 150–220 total | braced spears, towers, siege |

## Balance rules

1. No unit receives the best health, armour, speed, damage, and cost simultaneously.
2. Elite units must have at least one practical counter.
3. Faction bonuses modify a role; they do not erase the role's weakness.
4. Temporary or free units are weaker than paid units and cannot gather or build.
5. Cost and training time must be tested together; a cheap unit with a long train time is not equivalent to a cheap unit with mass production.

## Required test cases

- 10 units of each basic role versus the same role from each first-wave faction.
- 5 elite units versus 10 basic counters.
- 20-minute and 35-minute economy snapshots.
- Open terrain, forest, mountain/chokepoint, and coastal maps.
- Hero and wonder effects disabled first, then enabled separately.
