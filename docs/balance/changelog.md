# Balance Changelog

## Overview

This changelog records versioned balance revisions for the Tolkien 0 A.D. mod design documents. It tracks changes in numerical targets and rationale so that future tuning is traceable.

## Versioning scheme

- v0.1: initial numeric roster pass
- v0.2: post-audit tuning pass
- v0.3: pre-implementation balancing pass
- v0.4+: implementation-playtest tuning pass

## Current active version

v0.2

## v0.2 change summary

This revision reflects the cross-faction balance audit and tightens the most obvious value and counterplay issues before implementation.

### Rohan
- Reduced Éored Wedge charge bonus from +15% damage to +10% damage.
- Reduced turn-rate penalty to -20% rather than -25%.
- Kept Helm’s Horn as a short disruption effect, not a hard stun.
- Maintained defensive stakes as a specialist anti-cavalry tool, but reduced their durability against siege and fire.

### Lothlórien
- Reduced elevated-platform ranged bonus from +15% to +10%.
- Kept forest terrain advantages, but reduced platform safety to avoid permanent fortress-like protection.

### Erebor
- Capped Hoard of the Mountain bonus to a maximum of +10% late-game ranged/siege performance.
- Kept siege units expensive and slow to replace.
- Reduced the siege unit’s anti-large efficiency slightly to ensure direct counterplay remains meaningful.

### Iron Hills
- Reduced Iron Wall ranged-damage reduction from -20% to -15%.
- Reduced movement penalty from -20% to -15% to prevent the formation from becoming permanent and uninteractive.
- Kept repair support as a battlefield utility rather than a full siege reset tool.

### Númenor
- Reduced housing bonus from +15% to +10% maximum.
- Reduced elite health premium from +10% to +5% in early and mid-game comparisons.
- Kept coastal and stone infrastructure strong but not all-purpose.

### Harad & Umbar
- Reduced Corsair Plunder to 10–20% of unit or building value.
- Reduced desert speed bonus from +10% to +7% in open sand.
- Kept poison as a tactical attritional tool rather than a universal anti-infantry effect.
- Kept Mûmakil howdah fire modest and focused, not full-ranged artillery.

### Angmar
- Kept Barrow Plague at ~15% conversion chance for normal military deaths.
- Kept Thrall lifetime at ~45 seconds.
- Reduced Frost slow from -10% to -8% attack speed to keep Angmar from feeling like blanket melee suppression.

### Mordor
- Kept Blighted Desolation at a gather-rate reduction of ~15%.
- Kept the Eye reveal on a long cooldown and limited the search sweep to a region rather than a full-map persistent reveal.
- Maintained cheap Orc warfare but reduced the durability of base Orc Warriors to keep elite direct fights meaningful.

### Lindon
- Kept Gift of the West focused on naval, high-craft, and defensive techs only.
- Kept Swan Ship reinforcement capacity limited to a small infantry group or resource-supported transport role.

### Doriath
- Kept stealth and detection effects terrain-dependent.
- Reduced open-ground ambush value by keeping the ranger and guardian units more fragile in direct contact.

### Moria
- Kept Mithril Core yield at 50% of standard after depletion while structure remains active.
- Ensured tunnel entrances are still visible and can be blocked or disabled.
- Reduced tunnel movement bonus to +7% instead of +10% to keep the network from feeling like a free global route.

### Gondor & Arnor
- Kept Arnor’s Line Unbroken at +10% resistance in friendly territory.
- Kept Gondor’s stone bonus modest, avoiding permanent fortress-free domination.
- Kept the branch choice meaningful without creating a stronger version of the same roster.

## v0.2 active targets

These are the values that should be used as the active design baseline until the next audit pass.

The current active design files remain in `docs/unit-rosters/*.md` and the shared balance baseline remains in `docs/balance/unit-stat-baseline.md`.

## Next revision trigger

A new version should be created when:
- a full playtest pass occurs,
- a technology tree is added,
- the first-wave factions are implemented in test XML,
- or any faction mechanic proves too strong or too weak in practice.
