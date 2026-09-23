# Cross-Faction Balance Audit v0.1

## Purpose

This audit is a first structural pass to check whether the faction rosters are internally consistent before actual XML implementation begins. It compares value, power, counterplay, and role symmetry across factions.

The goal is not to lock final numbers. The goal is to catch obvious imbalance, missing counters, and role overlap before the team enters the implementation and AI tuning phase.

## Audit framework

The following checks are applied to every faction:

1. Basic infantry parity
2. Ranged unit parity
3. Anti-cavalry effectiveness
4. Elite infantry durability
5. Premium mobility and speed
6. Defensive strength in hold positions
7. Economy scaling and value-to-cost ratio
8. Temporary unit usefulness
9. Hero and wonder contribution
10. Counterplay readability
11. Map dependence
12. Strategic identity clarity

## Key rules for the audit

- Cost and power must remain proportional.
- Units with niche advantages must be weaker in other situations.
- Elite units cannot be both durable and cheap.
- Factions with stealth or control mechanics must have a clear counter, such as detection, focus fire, or force concentration.
- Heroes and wonders should not replace core faction role or create blanket immunity.
- Temporary units are a bonus, not a replacement for production.

## Audit findings by faction

### Lindon

Status: mostly coherent.

What works:
- elite quality and low replacement volume reads clearly;
- base infantry and archers are in the expected quality band;
- coastal and naval identity is distinct.

Potential problems:
- Gift of the West may be too broad if applied to every craft or tech;
- if Swan Ships are too cheap, Lindon becomes a low-risk transport and reinforcement faction;
- the champion can become an all-purpose elite when the faction already has high-quality infantry and archers.

Recommended adjustment:
- narrow the research bonus to high-craft, naval, and defensive technologies;
- cap Swan Ship reinforcement capacity to a small infantry group or require production cycle support;
- keep Lindon’s elite infantry stronger than baseline, but not above the top-tier Dwarven or Númenórean elites in all stats.

### Doriath

Status: mechanically coherent but fragile in open ground.

What works:
- stealth is distinct and effective in woodland maps;
- Doriath is built around map control, not mass combat.
- open-field weakness is a clear faction identity.

Potential problems:
- if forest detection is too strong, Doriath becomes uncounterable in all maps;
- if its range and damage are too high, the stealth mechanic becomes overvalued.

Recommended adjustment:
- keep stealth conditional and terrain-dependent;
- do not allow permanent unseen state through a single forest tile or a single structure;
- ensure ranger damage and armor remain lower than elite Dúnedain or elite Mordor infantry.

### Rohan

Status: likely the strongest cavalry identity, but the easiest faction to overvalue in a long battle.

What works:
- cavalry mobility and aggression are clear;
- stakes and camps give a unique defensive identity;
- Rohirrim and champion units are strong but readable.

Potential problems:
- if charge damage and speed are too high, Rohan becomes too dominant on open maps;
- if Field Camps are too strong, Rohan gets static defense without paying the cost of walls;
- if Helm’s Horn is too long or too devastating, the faction becomes too oppressive in a single engagement.

Recommended adjustment:
- limit Éored Wedge to short duration and moderate bonus;
- make stakes vulnerable to siege and fire;
- keep Helm’s Horn as a short disruption ability rather than a hard stun or fear lock.

### Mordor

Status: strong as a mass-pressure faction; must stay cheap and numerically oppressive.

What works:
- worker separation and the Snaga worker identity are readable;
- mass production and attrition are coherent;
- Wargs and Crebain support the faction's scavenger nature.

Potential problems:
- if Orc Warriors are too durable, the faction loses its intended weakness to elite direct fights;
- if Blighted Desolation is too strong, Mordor becomes a map-control tax on every enemy;
- if the Eye effect is too frequent or too broad, the faction becomes oppressive even when it is losing a fight.

Recommended adjustment:
- keep Orc Warriors low-health and low-armor;
- limit Blighted Desolation to gather-rate reduction and not destruction or debuff stacking;
- keep the Eye on a long cooldown and reduce the revelation duration if necessary.

### Moria

Status: coherent fortress identity, but needs strict limits on mobility and tunnel power.

What works:
- heavy infantry durability and tunnel movement read clearly;
- deep mineral and defensive strength are unique;
- Mithril Core is a practical faction identity rather than a gimmick.

Potential problems:
- tunnels may become too strong if they allow instant movement through map chokepoints;
- Mithril Core may become an economy sink that creates raw metal inflation;
- the faction risks being too slow and too protected if its elite infantry are both very durable and too cheap.

Recommended adjustment:
- keep tunnel movement limited to linked tunnel spaces and not all map travel;
- require active deep mining or tunnel infrastructure for the Mithril Core bonus;
- ensure elite units have anti-large or ranged counterplay.

### Gondor & Arnor

Status: very good branch design, but must avoid turning the branches into two versions of the same faction.

What works:
- shared Phase I and branching Phase II is strong;
- Arnor’s mobility and Gondor’s defense are distinct;
- both paths remain readable and understandable.

Potential problems:
- if the shared units are too strong, the branch choice becomes irrelevant;
- if Arnor’s stealth is too strong, it becomes a stronger Doriath clone;
- if Gondor’s tower and wall bonuses are too large, the faction becomes the default defense pick with no cost.

Recommended adjustment:
- keep shared units slightly below the strongest elite infantry in the mod;
- ensure Arnor and Gondor skill bonuses remain local to terrain or territory;
- do not let Gondor’s stone bonus make walls into an auto-win system.

### Lothlórien

Status: coherent and thematic, but likely underpowered if played away from woodlands.

What works:
- forest identity is strong and readable;
- ranged fire and topographic value are distinct;
- Mallorn and platform play are a cool fantasy expression.

Potential problems:
- towers and platforms may feel too safe if they are too difficult to attack;
- if the faction is too good in forests, it becomes map-dependent in a way that creates unfun matchups.

Recommended adjustment:
- keep platform accuracy and visibility strong, but not 100% safe;
- ensure the faction is weaker in open, flat battlefields;
- allow siege and direct attacks to punish platforms in a way that feels fair.

### Erebor

Status: good, but must avoid becoming a free artillery faction with no weakness.

What works:
- wealth and siege identity are distinct;
- Hoard bonus is a clear fantasy mechanic.
- siege units are powerful but should be slow and readable.

Potential problems:
- if Hoard bonus is too high, Erebor dominates without needing to fight; the faction becomes a stat machine rather than a tactical one;
- ballista and siege support may become too efficient if not slowed by construction or repair.

Recommended adjustment:
- cap the Hoard bonus at 10–15% total late-game performance increase rather than a direct damage multiplier;
- keep the siege units expensive and slow to replace;
- make Erebor’s open-field melee weaker than Dwarven strongholds in the early and mid-game.

### Iron Hills

Status: coherent but must avoid a stale “always braced” identity.

What works:
- shield-wall and war-wagon identity is strong and unique;
- formation play and repair support fit fantasy and gameplay.

Potential problems:
- if Iron Wall is too strong, the faction becomes a permanent defensive wall with little skill expression;
- if repair support is too efficient, the faction can repeatedly keep siege under control without meaningful risk.

Recommended adjustment:
- keep Iron Wall’s bonus local to range reduction and charge resistance, not broad damage immunity;
- require timely movement and forward pressure to use the formation efficiently.

### Númenor

Status: good quality faction, but must not become the “best of everything” human faction.

What works:
- elite infantry, infrastructure, and coastal identity are clear;
- the human quality curve is easy to read.

Potential problems:
- if all Númenórean units are too durable, the faction becomes a premium human monarchy with no meaningful weakness;
- if housing bonuses are too high, it becomes a population snowball.

Recommended adjustment:
- keep the health bonus modest and not universal;
- prevent a universal pop boost from being too strong;
- ensure Númenor is strongest in disciplined, prepared fights rather than chaotic attrition.

### Harad & Umbar

Status: strong thematic identity but needs a careful anti-large and anti-raiding balance pass.

What works:
- plunder, poison, desert mobility, and elephants are all distinct;
- Mûmakil are a memorable battlefield centerpiece;
- raiding pressure makes sense.

Potential problems:
- if plunder is too high, Harad becomes a free economy faction;
- if poison is too common, it becomes a universal answer to basic infantry;
- if Mûmakil are too durable or too cheap, they create a large auto-win scenario.

Recommended adjustment:
- cap plunder to a percentage of value and no more than a fraction of the target cost;
- keep poison focused on duration and damage over time, not stacking reliability;
- ensure Mûmakil are slow and vulnerable to siege, flanking, and focused fire.

### Angmar

Status: strong fantasy identity and unique mechanic, but the Black-Templar pressure cycle must be constrained.

What works:
- Barrow Plague, Frost, and Thrall creation feel unmistakably Angmar.
- the faction has a strong local battlefield identity and a dark fantasy feel.

Potential problems:
- if conversion chance is too high, Angmar becomes a free replacement army from any invaded body count;
- if Thralls are too strong or too cheap, they become a permanent economic engine;
- if Frost or local aura effects stack with other slow effects, it becomes unplayable for melee in certain maps.

Recommended adjustment:
- keep conversion at 15% for normal military casualties and lower for champions/siege;
- keep Thralls temporary and weak;
- do not allow aura effects to stack without clear visual feedback and a brief duration cap.

## Cross-faction audit summary

### Factions that are currently in a healthy state
- Lindon
- Doriath
- Mordor
- Moria
- Gondor & Arnor
- Angmar (with careful conversion and aura caps)

### Factions needing the most tuning
- Rohan (charge power and static defense)
- Lothlórien (forest dependence vs open-field weakness)
- Erebor (source of wealth and siege scaling)
- Harad & Umbar (plunder and Mûmakil power)
- Númenor (elite stack and housing)
- Iron Hills (formation strength and mobility)

## Immediate next actions

1. Lock the first playable faction baseline.
2. Tally all major cost/value differences within equivalent roles.
3. Tune out the most obvious unit- and mechanic-level outliers.
4. Write a formal balance changelog and versioned target list.
5. Prepare the shared XML and technology templates for the first playable wave.

## Final assessment

The roster design is now coherent enough for a serious balance audit. The major issues are not conceptual anymore—they are specific tuning problems: cost/value ratios, a few overpowered niche mechanics, and faction-specific map dependence.

The next phase should be focused on audit-driven tuning rather than additional concept creation.
