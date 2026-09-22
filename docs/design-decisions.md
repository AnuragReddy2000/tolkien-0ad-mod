# Design Decisions and Open Questions

This file records important decisions that should not be lost when the faction documents are shortened or rewritten.

## Confirmed decisions

- Documentation is split into a `docs/` folder and separate faction files.
- The standard 0 A.D. phase and resource loops remain intact.
- Númenor receives a modest health advantage over ordinary Men, not a universal superiority hierarchy.
- Rohan has no stone walls and uses stakes, field camps, and mobility instead.
- Helm Hammerhand has a horn intimidation ability.
- Harad Mûmakil are based on established Indian war-elephant implementations and can garrison archers in howdahs.
- Corsair Plunder is distinct from ordinary loot because it targets profitable units and buildings and awards only a fraction of value.
- Mordor’s Blighted Desolation is a miasma that reduces enemy gathering efficiency, not a farm-destruction mechanic.
- Mordor has Crebain for reconnaissance and Wargs for reconnaissance and harassment.
- Mordor uses the powerful hybrid All-Seeing Eye: brief global reveal followed by a long search, with a long cooldown.
- Khamûl replaces the Mouth of Sauron in the standard Mordor hero roster.
- Saruman is reserved for Isengard, an alliance, or a scenario.
- Angmar’s Barrow Plague converts only eligible enemy military deaths; own units do not convert.
- Barrow Plague has an approximately 15% base chance and temporary controllable Thralls with approximately 45-second lifetime.
- Barrow Plague does not require a separate hard population cap; deaths, conversion probability, and TTL impose the natural limit.

## Open technical questions

- Whether the engine can implement a moving reveal cone cleanly and deterministically.
- Whether Mûmakil howdah units can fire while moving and receive damage through the host unit.
- How to implement terrain-sensitive stealth and territory-based gathering penalties without excessive scripting.
- Whether tunnel networks require engine support beyond templates and territory logic.
- Whether death-triggered Thrall creation can reliably identify eligible units and prevent duplicate triggers.
- Which effects should be represented through templates, technologies, aura components, or scripts.

## Balance testing targets

All numeric values are starting points, not final commitments. Test them in isolated scenarios before integrating them into full faction matchups.
