# Implementation Roadmap

## Goal

Build the Tolkien 0 A.D. total-conversion mod in small, testable stages. The goal is not to implement every faction at once. The goal is to establish a stable core loop, then add faction identity and content in measured iterations.

## Phase 0 — Foundation and tooling

### Objectives
- Confirm target 0 A.D. version and compatible tooling.
- Establish repo structure and template flow.
- Define shared XML, script, and asset conventions.
- Set up a small test map and a baseline AI profile.

### Deliverables
- Working template for buildings, units, techs, wonders, and heroes.
- Shared definitions for economy, phase progression, and faction metadata.
- Clear process for unit balance testing and AI role tagging.

## Phase 1 — Shared systems prototype

### Required shared systems
- Standard resource loop with food, wood, stone, and metal.
- Village/Town/City phase gating.
- Worker assignment and urban building flow.
- Basic building, unit, and tech definitions.
- Hero template and wonder template.
- Territory and visibility basics.
- Initial garrison and formation behavior.

### Critical prototype tasks
- Confirm how custom movement, visibility, and aura effects can be implemented.
- Ensure worker roles and resource gathering remain readable to players.
- Test the interaction between terrain, visibility, and faction identity.

## Phase 2 — First playable faction set

### Choose the first six factions
1. Lindon
2. Doriath
3. Rohan
4. Mordor
5. Moria
6. Gondor & Arnor

### Why this set
It covers the most distinct game identities while testing the following systems:
- ranged and elite infantry
- stealth and hiding
- cavalry mobility
- attrition and industrial pressure
- subterranean logistics
- branch-based faction mechanics

### Initial milestone
By the end of this phase, the project should have:
- six playable civilizations;
- shared economy and phase structure;
- a clear first-wave roster for each civilization;
- testing notes for matchups and counterplay.

## Phase 3 — Shared mechanics validation

### Prototype and validate these systems before broad expansion
- Mûmakil howdah garrison behavior.
- Mordor’s Blighted Desolation gather-rate penalty.
- The Eye of Sauron reveal system.
- Barrow Plague conversion and temporary Thrall lifecycle.
- Rohan’s stakes, field camps, and Éored Wedge.
- Doriath’s territorial concealment and detection penalties.
- Moria tunnel logistics and capture behavior.

### Risks to watch
- reveal effects that are too broad or too opaque;
- economy events that feel arbitrary rather than tactical;
- thresholds that are too generous and cause snowballing;
- temporary units that are too strong or too permanent.

## Phase 4 — Second-wave factions

### Add in this order
1. Harad & Umbar
2. Erebor
3. Iron Hills
4. Númenor
5. Angmar
6. Lothlórien

### Why this order
These are either more specialized or more tightly coupled to shared systems already proven in the first wave.

## Phase 5 — Balance pass and AI tuning

### Objectives
- Compare faction performance in low-level and mid-level matches.
- Tune economic bonuses, unit production costs, and visibilities.
- Ensure each faction has a clear early-game weakness and a meaningful late-game strength.
- Adjust AI priorities for specialized factions.

### Deliverables
- unit comparison notes by faction pair;
- map-specific notes for forest, desert, mountain, coast, and interior terrain;
- AI build-order recommendations for each faction.

## Phase 6 — Polish and release prep

### Final goals
- improve visual clarity and UI cues for faction mechanics;
- tune heroes and wonders for readability;
- finalize balanced first-wave faction roster;
- produce the first public vertical slice.

## Recommended technical priorities

### Engine-critical mechanics
- temporary units and decay timers;
- aura-based effects and target filtering;
- reveal cone and search radius logic;
- garrison and howdah architecture;
- territory-driven gather penalties;
- conditional stealth and detection behavior;
- formation-based movement and impact modifiers.

## Suggested milestone schedule

### Milestone A — Core template ready
Weeks 1–3

### Milestone B — First six factions playable
Weeks 4–10

### Milestone C — First balanced test build
Weeks 11–16

### Milestone D — Expansion wave 2 ready
Weeks 17–22

### Milestone E — Public vertical slice
Weeks 23–28

## Summary

The project should proceed by proving the shared 0 A.D. loop and testing the hardest custom mechanics first. The first wave of factions is designed to validate the most complicated systems: stealth, reveal, temporary undead, Mûmakil garrison, tunnel logistics, and cavalry charges.
