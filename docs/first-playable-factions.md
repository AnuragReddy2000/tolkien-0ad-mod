# First Playable Factions

## Target set

The first playable faction set should be:

1. Lindon
2. Doriath
3. Mordor
4. Moria
5. Númenor

> Revised from the original six-faction set: Rohan and Gondor & Arnor moved to the
> second wave, and Númenor promoted into the first wave because its implementation
> is already underway. Rohan is deferred (no cavalry roster yet); Gondor & Arnor's
> branch mechanic is deferred to a later pass.

## Rationale

This set covers the widest spread of mechanics while staying feasible for a first implementation pass.

### Lindon
- elite infantry and maritime identity
- controlled research and coastal play
- low-risk, high-quality unit set

### Doriath
- stealth and territorial concealment
- great for testing terrain-driven detection, hidden units, and ambush mechanics

### Mordor
- mass production, industrial pressure, and a reveal mechanic
- tests worker separation, attrition, and late-game ability timing

### Moria
- tunnel logistics and fortress durability
- tests underground movement and defensive lines

### Númenor
- elite infantry, maritime power, and fortified-haven durability
- tests naval production, housing, and passive civ-bonus stacking (no scripted active mechanic required)

## Implementation order

1. Lindon (implemented)
2. Doriath (implemented)
3. Moria (implemented)
4. Númenor (implemented)
5. Mordor (next — art assets already present)

## Art strategy (deprioritized)

Custom art is deferred for the first wave. All units and structures reuse existing
vanilla 0 A.D. art via the fixed per-faction architecture mapping recorded in
`docs/design-decisions.md` (Lindon → Athenian/Hellenic/Spartan stone, Númenor →
Roman/Hellenic marble, Moria → Maurya pillared stone + Germanic timber, Mordor →
Kushite dark stone + Carthaginian mass, Doriath → Celtic/Gallic woodland). The
custom heads, weapons, and skins already committed stay in the repo but are not a
first-wave gate; no new custom meshes or textures are produced until the slice
plays clean on reused art.

## Release target

The first public build should be a vertical slice with these five factions and a small set of basic maps. After balance and gameplay validation, the second wave should expand the roster (Rohan, Gondor & Arnor, and the remaining factions).