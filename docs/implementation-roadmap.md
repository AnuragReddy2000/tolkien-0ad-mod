# Implementation Roadmap

## Phase 1: Repository and mod skeleton

- Establish the mod directory and metadata.
- Define shared templates for units, buildings, technologies, heroes, and wonders.
- Confirm supported 0 A.D. version.
- Add a minimal test civilization and one test map.

## Phase 2: First playable faction set

Recommended initial set:

1. Lindon
2. Doriath
3. Rohan
4. Mordor
5. Moria
6. Gondor & Arnor

This set tests naval, stealth, cavalry, mass production, tunnels, and branching faction design.

## Phase 3: Shared systems

Implement and test:

- faction metadata and phase progression;
- territory-dependent effects;
- formations and stances;
- hero abilities;
- wonder abilities;
- transport and garrison behavior;
- temporary units and decay;
- scouting and reveal effects.

## Phase 4: Faction content

Add structures, units, technologies, heroes, and wonders in small vertical slices. Each slice should be playable before the next faction begins.

## Phase 5: Balance and AI

- Establish baseline unit comparisons with ordinary 0 A.D. units.
- Add AI role metadata and build-order support.
- Test faction matchups and map dependence.
- Tune passive economies and free/temporary units carefully.

## Phase 6: Second-wave factions

Add Erebor, Iron Hills, Númenor, Harad & Umbar, and Angmar after the first faction set is stable.

## First technical risks

- Moving reveal cone for the All-Seeing Eye.
- Mûmakil howdah garrison and firing behavior.
- Tunnel entrance logistics and capture behavior.
- Temporary Thralls and death-trigger conversion.
- Terrain and territory-dependent stealth or gathering effects.

Each risk should receive a small isolated prototype before full faction production.
