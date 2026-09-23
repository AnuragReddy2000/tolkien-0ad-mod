# Detailed Execution Plan and Handoff

## 1. Purpose

This document is the implementation handoff for the Tolkien 0 A.D. mod. It converts the completed design, roster, and balance work into an executable engineering sequence for the next contributor or team.

The implementation must proceed in vertical slices. Do not attempt to implement all twelve factions, all heroes, or all custom mechanics at once.

## 2. Current project status

Completed:

- Repository and documentation structure.
- Twelve faction design documents.
- Shared design principles and recorded design decisions.
- First playable faction set.
- Numeric v0.1 rosters for all twelve factions.
- Cross-faction balance audit.
- Active v0.2 balance targets and changelog.

First playable factions:

1. Lindon
2. Doriath
3. Rohan
4. Mordor
5. Moria
6. Gondor & Arnor

Not yet implemented:

- 0 A.D. mod metadata and executable mod structure.
- XML entity templates.
- Technologies and phase progression.
- Faction selection and civilization data.
- JavaScript or engine-side custom mechanics.
- Art, audio, UI, localization, AI, maps, and automated tests.

## 3. Non-negotiable design constraints

- Preserve the normal 0 A.D. Village, Town, and City phase loop.
- Preserve Food, Wood, Stone, and Metal as the primary resources.
- Keep ordinary 0 A.D. counters recognizable.
- Every faction bonus must have a practical counter.
- Do not implement placeholder global buffs when a local or conditional effect is intended.
- Use the active v0.2 values as targets, but expect changes after playtesting.
- Record every balance change in `docs/balance/changelog.md`.
- Do not add a custom mechanic until its fallback behavior is defined for unsupported engine features.
- Separate lore/design assumptions from confirmed engine capabilities.
- **All simulation-affecting randomness must use the engine's deterministic, seeded simulation RNG. Never use `Math.random()` or another unsynchronized random source in simulation code.**

## 4. Repository and mod structure to establish

The implementer should first confirm the target 0 A.D. version and create the actual mod using the version-appropriate metadata format. The paths below are the expected 0 A.D. layout for the target implementation and should be validated against the selected release only if that release has a documented structural difference.

```text
mod-root/
├── mod.json
├── README.md
├── LICENSE
├── simulation/
│   ├── components/
│   ├── helpers/
│   ├── ai/
│   ├── data/
���   │   ├── civs/
│   │   └── technologies/
│   └── templates/
│       ├── structures/
│       └── units/
│           ├── <civ>/
│           │   ├── infantry/
│           │   ├── cavalry/
│           │   ├── siege/
│           │   ├── ships/
│           │   └── heroes/
│           └── common/
├── art/
├── audio/
├── gui/
├── maps/
├── l10n/
└── tests/
```

Use `simulation/data/technologies/` for technology definitions and `simulation/data/civs/` for civilization data. Use `simulation/ai/` for AI code. Put structures under `simulation/templates/structures/`; ships and siege are unit templates under `simulation/templates/units/<civ>/ships/` and `simulation/templates/units/<civ>/siege/`, not sibling template categories. Keep the logical grouping above even if the selected 0 A.D. release requires a small naming variation.

## 5. Workstream A — engine and toolchain validation

### Tasks

1. Record the supported 0 A.D. version.
2. Install or document the matching mod development tools.
3. Create a minimal mod that appears in the mod selector.
4. Load one custom civilization or one custom unit.
5. Verify XML validation, hot reload, log output, and error reporting.
6. Document how to launch a test match and collect logs.
7. Establish a formatting and naming convention.
8. Confirm the available deterministic RNG API and document its correct simulation-side usage.
9. Add a two-peer lockstep smoke test before implementing scripted randomness.

### Exit criteria

- The mod loads without errors.
- A custom test unit can be spawned and selected.
- A test technology can be researched.
- The team can reproduce a clean test match from a new checkout.
- Two identical simulations remain synchronized while exercising a deterministic random test mechanic.

## 6. Workstream B — shared data and template foundations

### Implement first

- Faction metadata and civilization selection.
- Shared resource definitions.
- Phase I/II/III requirements.
- Common worker template.
- Basic infantry template.
- Spearman template.
- Archer template.
- Scout template.
- Cavalry template.
- Siege template.
- Hero template.
- Wonder template.
- House/population template.
- Civic Center template.
- Barracks, stable, range, dock, workshop, tower, wall, and market templates.

### Template inheritance rules

- Put common attributes in shared parent templates.
- Put faction-specific values in faction child templates.
- Avoid copying entire templates when one inherited override is sufficient.
- Keep names, icons, sounds, and selection text separate from combat logic.
- Use one canonical template for each balance role so cross-faction changes are easy to audit.

### Exit criteria

- Each shared role can be spawned in a sandbox match.
- Phase transitions work.
- Costs, population, health, armour, attack, range, speed, and training time display correctly.
- A technology can modify a shared unit without corrupting unrelated units.

## 7. Workstream C — first vertical slice

Implement only the minimum playable content first:

- one Civic Center per faction;
- one worker;
- one house;
- one resource drop-off or economic structure;
- one barracks or equivalent;
- one basic infantry unit;
- one ranged or specialist unit where appropriate;
- one Town phase technology;
- one City phase technology;
- one test hero only after the unit loop is stable;
- no final wonders in the first slice.

### Recommended implementation order

1. Lindon basic infantry and archer.
2. Doriath basic infantry and conditional stealth prototype.
3. Rohan scout, spearman, and rider.
4. Mordor Snaga, Orc Warrior, and Orc Spearman.
5. Moria Guardsman and tunnel placeholder.
6. Gondor/Arnor shared recruit, spearman, and archer.

### Vertical-slice acceptance criteria

- Six civilizations can start a match.
- Workers gather all required resources.
- Each faction can reach Town phase.
- Each faction can produce a basic military force.
- Each faction can destroy another faction's military and economic structures.
- No faction relies on an unimplemented signature mechanic to function.

## 8. Workstream D — faction implementation

Each faction must be implemented using the same checklist.

### Faction checklist

1. Civilization metadata and starting resources.
2. Phase requirements and phase technologies.
3. Civic Center, houses, dropsites, and economic buildings.
4. Military production buildings.
5. Basic units.
6. Advanced units.
7. Elite units.
8. Siege and naval units where applicable.
9. Faction technologies.
10. Hero roster and abilities.
11. Wonder and wonder ability.
12. UI icons, tooltips, sounds, and localization keys.
13. AI build order and unit-role metadata.
14. Sandbox test scenario.
15. Balance report and changelog entry.

### Implementation order for first wave

#### Lindon

Start with infantry, archer, dock, and Gift of the West. Add Swan Ships only after ordinary transport and naval behavior is confirmed.

#### Doriath

Start with forest camouflage on stationary units. Add Girdle of Melian as a local territory effect after detection and stealth behavior is tested.

#### Rohan

Start with scout, spearman, rider, and pasture. Add stakes and Field Camps next. Implement Éored Wedge only after ordinary cavalry charge behavior is stable.

#### Mordor

Start with Snaga workers and Orc mass production. Add Wargs and Crebain. Implement Blighted Desolation and the All-Seeing Eye as separate prototypes.

#### Moria

Start with durable infantry and deep mining. Implement tunnels as a separate prototype before making them central to the faction's build order.

#### Gondor & Arnor

Implement the shared Phase I roster first. Add the Phase II branch choice only after the shared faction is playable. Lock access to incompatible branch upgrades.

## 9. Custom mechanic prototypes

Each prototype must have a minimal test map, debug output, fallback, and acceptance criteria.

### Doriath camouflage and Girdle

- Trigger: unit stationary in suitable forest or local faction territory.
- Break conditions: attack, damage, construction, invalid terrain, or movement.
- Counterplay: detection, area damage, fire, scouting, and territory capture.
- Acceptance: concealment is readable, reversible, and never global by accident.

### Rohan cavalry and Field Camps

- Charge bonus applies once per cooldown, not continuously.
- Éored Wedge target: +10% charge damage, -20% turn rate.
- Stakes must be vulnerable to infantry, fire, and siege.
- Field Camps must not replace Civic Centers or become unrestricted production hubs.
- Acceptance: cavalry is dangerous in open terrain but loses to prepared counters.

### Mordor Blighted Desolation

- Target only enemy worker gathering inside affected territory.
- Target penalty: approximately 15% gather efficiency.
- No resource-node destruction.
- No stacking from overlapping structures unless explicitly tested.
- Acceptance: the penalty is visible and disappears when territory or gathering conditions disappear.

### Mordor All-Seeing Eye

Preferred behavior:

1. Approximately 5 seconds of global reveal.
2. Approximately 30–45 seconds of regional search.
3. Long cooldown around 8 minutes.
4. Warning and visual feedback for all players.
5. Barad-dûr must remain standing.

Fallback: approximately 15 seconds of global reveal with an 8–10-minute cooldown if a moving search cannot be implemented reliably.

### Moria tunnels

- Linked entrances only.
- Entrances visible and attackable.
- Entrances can be blocked, captured, or disabled.
- No unrestricted global teleport.
- Target tunnel movement bonus: +7%.
- Acceptance: tunnel networks create logistics decisions without removing map control.

### Harad Mûmakil

- Use the engine's existing elephant or garrison architecture where possible.
- Target: approximately 500 HP, 3 population, slow movement, high cost.
- Howdah capacity target: 3–4 archers.
- Crew receives modest range/sight support, approximately +10–20% range.
- Elephant death must expose or otherwise account for the crew.
- Fallback: ordinary transport/garrison behavior if moving howdah fire is not reliable.

### Angmar Barrow Plague

- Trigger only on eligible enemy military deaths inside an Angmar aura.
- Normal military conversion target: approximately 15%.
- Lower chance for champions and siege; exclude heroes, workers, summons, and Angmar units.
- Thrall target: 45-second lifetime, weak stats, no gathering/building/capturing/garrisoning, controllable.
- Prevent chain conversion.
- Use only the engine's seeded deterministic simulation RNG for the conversion roll; never use `Math.random()`.
- Acceptance: Thralls cannot become a permanent free army through a single battle, and identical lockstep simulations produce identical conversions.

## 10. Heroes and wonders

Implement heroes only after their faction's ordinary units are stable.

### Hero requirements

- One clear role.
- One or two signature abilities.
- Explicit cooldown and duration.
- Local or conditional aura where possible.
- Counterplay and vulnerability.
- No universal stacking of health, damage, armour, speed, and regeneration.

### Wonder requirements

- Requires City phase and meaningful resources.
- Has a visible strategic identity.
- Does not provide permanent global immunity or an unanswerable economy multiplier.
- Can be attacked, disabled, or denied.
- Has a clear UI description and warning state.

## 11. Technology implementation

Create technology tables before XML implementation for each faction:

- technology name;
- phase;
- prerequisite building;
- cost;
- research time;
- affected templates;
- modifier;
- stacking rule;
- counterplay or opportunity cost.

At minimum, each first-wave faction needs:

- one economic technology;
- one infantry or ranged technology;
- one faction identity technology;
- one Town-to-City technology;
- one late-game technology.

Do not implement a technology that only exists to grant an undocumented global statistic.

## 12. AI and map support

### AI requirements

- Starting build order for each first-wave faction.
- Worker distribution priorities.
- Phase-up conditions.
- Unit production priorities.
- Response to cavalry, siege, stealth, and monsters.
- Use of faction mechanics.
- Branch selection for Gondor/Arnor.

### Maps

Create or configure test maps for:

- open plains;
- dense forest;
- mountain/chokepoint;
- coastal map;
- mixed terrain.

Every map-dependent faction must be tested on both favorable and unfavorable maps.

## 13. Testing and quality gates

### Automated or repeatable checks

- XML/template validation.
- Missing asset and localization-key checks.
- Invalid parent-template checks.
- Technology prerequisite checks.
- Spawn-all-units sandbox test.
- Phase progression test.
- Population and cost test.
- Save/load test where custom scripts are involved.
- **Two-peer lockstep determinism test for every simulation script that uses randomness or time-based state.**
- **Repeat the same seeded scenario and verify identical random outcomes, entity creation, deaths, resources, and final state.**
- **Static check or code review gate that rejects `Math.random()`, wall-clock time, local machine state, or unsynchronized iteration as simulation inputs.**

### Manual balance tests

- Equal population: basic units versus equivalent roles.
- Equal resources: complete army comparisons.
- 20-minute economy snapshot.
- 35-minute economy snapshot.
- Hero disabled/enabled comparison.
- Wonder disabled/enabled comparison.
- Favorable and unfavorable terrain comparison.
- Rush, defensive, raid, and late-game scenarios.
- Repeat scripted-random scenarios with identical seeds and compare replays or state hashes where supported.

### Bug report minimum

Every issue should include:

- game version;
- mod commit;
- map;
- players and civilizations;
- reproduction steps;
- expected behavior;
- actual behavior;
- log excerpt;
- screenshots or replay where useful;
- whether the issue reproduces in a two-peer lockstep test.

## 14. Balance process

1. Use `docs/balance/v0.2-active-targets.md` as the initial target.
2. Implement one role or mechanic at a time.
3. Test without heroes and wonders first.
4. Compare equal-resource and equal-population results.
5. Adjust the smallest number of variables possible.
6. Record the change and reason in `docs/balance/changelog.md`.
7. Create v0.3 only after the first implementation playtest cycle.
8. Never silently change a roster value in code without updating the design document.

## 15. Suggested execution milestones

### Milestone 1 — Mod loads

Deliverables: metadata, minimal test unit, clean logs, documented launch instructions.

### Milestone 2 — Shared core works

Deliverables: resources, workers, phases, houses, basic buildings, shared unit templates.

### Milestone 3 — Six-faction skeleton

Deliverables: six civilizations start, gather, build, phase, and train basic units.

### Milestone 4 — First-wave vertical slice

Deliverables: signature mechanic prototype for each first-wave faction, one map per major terrain type, basic AI support.

### Milestone 5 — Heroes, technologies, and wonders

Deliverables: one tested hero and identity technology per faction, followed by wonders after core balance is stable.

### Milestone 6 — Balance and release candidate

Deliverables: repeatable test matrix, balance changelog, bug triage, localization pass, minimum art/audio/UI pass, and a reproducible packaged build.

## 16. Handoff checklist

The next contributor should not begin by adding random units. They should:

- read `docs/overview.md`;
- read `docs/design-principles.md`;
- read `docs/design-decisions.md`;
- read `docs/first-playable-factions.md`;
- read `docs/balance/cross-faction-audit.md`;
- read `docs/balance/changelog.md`;
- read `docs/balance/v0.2-active-targets.md`;
- read the relevant faction and roster files;
- confirm the target 0 A.D. version;
- create the minimal loading mod;
- confirm the actual `simulation/data/technologies/`, `simulation/data/civs/`, `simulation/ai/`, `simulation/templates/structures/`, and `simulation/templates/units/` paths;
- report engine limitations before changing the design;
- document and test the deterministic RNG API before implementing Barrow Plague or any other scripted random mechanic.

## 17. Definition of done for the first public vertical slice

The first public vertical slice is complete only when:

- six factions are selectable and playable;
- all factions use the standard resource and phase loop;
- each faction has at least one recognizable signature mechanic;
- all implemented mechanics have visible counterplay;
- basic units and structures have tested costs and timings;
- the game can be played without script errors;
- AI can complete a basic build order for each faction;
- test maps cover open, forest, mountain, and coastal conditions;
- known limitations are documented;
- balance changes are recorded and versioned;
- scripted random mechanics pass two-peer lockstep determinism tests;
- the build can be reproduced from the repository by another contributor.

## 18. Known risks and fallback decisions

- If a moving reveal cone is unreliable, use a timed global reveal.
- If Mûmakil howdah fire while moving is unreliable, use static firing or ordinary transport behavior.
- If tunnel traversal requires engine changes, begin with linked transport points or a temporary movement prototype.
- If territory-based worker penalties are too expensive to calculate, use aura regions around major structures as a controlled approximation.
- If death-triggered conversion is unreliable, prototype a manual or periodic eligible-death queue before attempting a fully reactive script.
- If terrain-sensitive stealth is not available, use stance- and position-based camouflage with explicit visual feedback.
- **If a custom random mechanic cannot use the engine's seeded simulation RNG, do not implement it with `Math.random()`. Replace it with a deterministic queue, fixed seeded lookup, periodic deterministic roll, or a non-random fallback and document the deviation.**
- **Do not use wall-clock time, network state, filesystem state, unordered external data, or unsynchronized native code to influence simulation outcomes.**

## 19. Final handoff expectation

The implementation owner is expected to return:

- supported engine version;
- working mod skeleton;
- implemented feature list;
- unsupported feature list;
- test results;
- known bugs;
- balance changes from v0.2;
- updated changelog;
- determinism test results and any RNG limitations;
- next milestone estimate.

The design is ready for implementation, but numeric values remain targets until tested in the actual engine. Engine limitations must be documented and resolved through the listed fallbacks rather than silently changing the intended faction identities.
