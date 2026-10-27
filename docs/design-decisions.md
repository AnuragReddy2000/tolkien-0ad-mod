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
- Mordor has Crebain for reconnaissance. Mordor fields no Wargs or Warg Riders (lore): its only cavalry are hired Variag horse-archers of Khand, trained at the Civic Centre.
- Mordor uses a search-only All-Seeing Eye: a rotating regional search on a long cooldown, with no global map reveal. Sauron's attention is finite (lore), and the engine has no shroud-reveal script API (global reveal would also risk vision-range perf costs).
- Khamûl replaces the Mouth of Sauron in the standard Mordor hero roster.
- Saruman is reserved for Isengard, an alliance, or a scenario.
- Angmar’s Barrow Plague converts only eligible enemy military deaths; own units do not convert.
- Barrow Plague has an approximately 15% base chance and temporary controllable Thralls with approximately 45-second lifetime.
- Barrow Plague does not require a separate hard population cap; deaths, conversion probability, and TTL impose the natural limit.
- Victory conditions follow vanilla 0 A.D.: standard maps use conquest victory, and relic and wonder map behavior is unchanged.
- The First, Second, and Third Ages are not a design constraint. Factions from different ages coexist without a unified timeline premise, and age accuracy does not drive gameplay decisions.
- The target engine is the latest stable release of 0 A.D. at the time implementation begins.
- Building art reuses vanilla architecture sets with a fixed per-faction mapping (all sets verified present in vanilla; mixing within a faction is allowed but each faction must read distinctly at a glance):
  - Lindon: Athenians + Hellenes, Spartans stone for tower/fortress (maritime classical).
  - Númenor: Romans + Hellenes marble (peak imperial sea-kings; Roman distinguishes it from Lindon's Greek).
  - Gondor: Macedonians + Romans for fortress/white stone (martial successor-state).
  - Arnor: Britons + weathered Roman remnants (diminished northern Dúnedain).
  - Rohan: Germans + Gauls halls (timber mead-halls; no stone walls per above).
  - Moria: Carthaginians (all standard structures; custom tunnel mouth, deep-shaft mine, and vaults wonder kept).
  - Erebor: Seleucids + Persian gold accents (eastern monumental treasure-halls).
  - Iron Hills: Germans stone + Macedonians military (dark iron Dwarves; distinct from Erebor and Moria).
  - Lothlórien: Britons light wood + Hellenes silver/white (distinct from Doriath's Celts).
  - Doriath: Celts + Gauls woodland (wooden watchtower instead of a stone defense tower, matching its fragile-but-prepared identity).
  - Mordor: Kushites dark stone + Carthaginian mass (volcanic brutalism).
  - Angmar: Britons cold stone + Germans fell timber (distinct from Rohan's Germanic timber).
  - Harad & Umbar: Ptolemies desert + Carthaginians ports + Mauryas Mûmakil pens + vanilla pirate ships for Umbar corsairs.
- The `tolkien_test` fixture civ stays architecturally generic; the mapping applies to real factions only.

## Proposed concepts

- Gondor-path Civic Centre upgrade: wall-mounted catapults provide fixed defensive fire at shorter range than regular catapults. The upgrade is branch-exclusive and can be active on only one Civic Centre per player at a time; phase, cost, and balance values remain open.

## Open technical questions

- Whether the engine can implement a moving reveal cone cleanly and deterministically.
- Whether Mûmakil howdah units can fire while moving and receive damage through the host unit.
- How to implement terrain-sensitive stealth and territory-based gathering penalties without excessive scripting.
- Whether tunnel networks require engine support beyond templates and territory logic.
- Whether death-triggered Thrall creation can reliably identify eligible units and prevent duplicate triggers.
- Which effects should be represented through templates, technologies, aura components, or scripts.

## Balance testing targets

All numeric values are starting points, not final commitments. Test them in isolated scenarios before integrating them into full faction matchups.
