# Top-Level Implementation Notes

## Shared system notes

These notes apply to all factions and should be treated as baseline implementation requirements.

- Keep the standard 0 A.D. phase structure.
- Preserve the vanilla economy model.
- Pair strong mechanics with clear counterplay.
- Avoid broad static buffs that make all units utility if one structure remains standing.
- Use visible and readable UI cues when a faction mechanic is active.
- Prefer local or terrain-based effects where possible.

## Important engine features to prototype early

- aura filtering and target checks
- temporary unit lifecycles and decay
- howdah garrison behavior
- territory-based gather penalties
- reveal effect and search cone logic
- conditional stealth and detection systems
- movement and formation modifiers tied to a specific stance or unit state

## Balance principles for the first public release

- strong factions can win by timing and terrain, not just through permanent stat inflation;
- temporary units are a bonus, not a replacement for real production;
- each wonder should read clearly and feel powerful without becoming a universal answer;
- heroes should support a role rather than stack every stat category at once.
