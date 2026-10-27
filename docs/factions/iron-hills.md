# Iron Hills

## Identity

The Iron Hills are a disciplined heavy-formation Dwarven faction defined by shield walls, low movement, and durable field engineering.

## Core mechanics

### Iron Wall formation
Iron Wall is a tactical defensive stance that reduces ranged damage and resists charge disruption at the cost of movement and flexibility.

Finalized (Phase II Barracks unlock, designated heavy infantry, stance breaks if dispersed/retreating, no attack bonus): chat 40–55% ranged reduction + strong (not immune) trample resist, -35–45% move, reduced turn. Active v0.2 (overrides — use this): -15% ranged damage, -15% movement. v1 75% reduction + immunity + -50% move shelved. Roster v0.1 still lists -20%/-20% — stale, update to v0.2.
Counters: flanks, siege, massed ranged, forced split, mobility denial.

### Cavalry (none by design)
Dáin's warriors rode ponies to battle but always dismounted to fight — no mounted combat, no cinematic goat/boar riders (per `cavalry_recommendations.md`).

Finalized: shares Erebor's Pack Pony + Crippling Shot hunting package; the roster differentiates through Iron Wall phalanxes, forward siege, and discounted watchtowers (see above/below).

### Repair support
The faction repairs siege engines and war-wagons more rapidly than standard citizen units. This fits the Dwarven identity and keeps the normal 0 A.D. repair system intact.

Finalized — Mechanized Logistics: citizen-soldiers repair siege/ballistae/war-wagons 25% faster; standard restrictions + diminishing returns apply; disabled/heavily reduced while target under attack; may cost Wood/Metal. Moving-repair via Field Engineering deferred. Not a siege reset tool.

### Stone-built structures
Initial balance proposal: for ordinary buildings whose construction is wood-heavy and lore-appropriate as stonework, replace half the Wood cost with Stone while keeping the combined resource cost unchanged. For example, a 150-Wood House becomes 75 Wood + 75 Stone, and a 100-Wood Storehouse becomes 50 Wood + 50 Stone. Leave wood-intensive workshops and siege infrastructure alone, and avoid adding Stone to buildings that already have a substantial Stone cost.

Do not add a dedicated Stone-mining technology yet. Playtest the building-cost shift first; if Stone becomes a sustained bottleneck, consider a modest mining-rate technology.

### Siege (per `siege_recommendations.md`)
Engineering powerhouse — shared Dwarven doctrine with Erebor, tuned for forward holding.
Finalized: heavily armored Battering Rams (most durable class, pairs with Iron Wall + forward play); Iron-Head Bolt Thrower (Heavy Ballista, line-piercing bolts) implemented as Heavy Field Ballista (stationary, setup time, needs escort); Mobile War-Wagon Phase II/III fire support kept distinct from true siege. Discounted watchtowers + repair bonus sustain siege pushes.

## Strengths

- durable front-line infantry
- strong defensive hold
- war-wagons and field siege support
- great for controlled, deliberate battles

## Weaknesses

- slow movement and poor pursuit
- vulnerable to flanks and cavalry disruption
- weak in rapid reaction and mass raids

## Structures

- stronghold-like production; repair yards; wagons and siege support; defensive halls; field fortifications.

Finalized tree (kept): Phase I — CC, House, Storehouse, Farmstead, Field, Outpost. Phase II — Barracks, Market, Blacksmith, Heavy Bolt Tower (slow, expensive Metal, strong vs heavy, weak to siege/flank), Stone Wall. Phase III — Great Foundry (Fortress), Temple, Great Bastion.

## Units

- shield infantry; heavy melee line; war-wagons; siege support; elite Dwarven defenders.

Finalized: Shield-bearer (durable basic, formation-dependent), Miner (worker + mining/construction/repair, weak combat), Champion Mattock Vanguard (elite anti-structure/armored, slow expensive, weak ranged/cav), Heavy Field Ballista (stationary siege, setup time, needs escort), Mobile War-Wagon Phase II/III (fires on move at lower accuracy, poor turn, no close fire, weak cav/melee/siege). Shares Erebor's Pack Pony + Crippling Shot hunting package. No Stables, no mounted units.

## Heroes

- fortress commander; formation hero; support hero with local repair or morale effects.

Finalized (local only): Grór (~+25% nearby war-wagon/engine armor; double-armor shelved), Frór (nearby Iron Wall reflects 5–10% melee while in formation), Náin II (~+20–25% baseline-infantry train speed at nearby Barracks, no stacking).

## Wonder

The wonder should anchor a defensive strongpoint without becoming an invulnerable fortress.

Finalized — Great Bastion of the East: very-high-but-finite HP, 2–3 built-in ballistae, garrison capacity (stronger full), nearby Iron Wall gains modest cohesion/resist. Fallback if built-ins hard: unlock improved ballistas + faster deploy/repair + local command aura.

## Counterplay

Use flanks, cavalry, range, and siege pressure to force the formation to split or collapse.
