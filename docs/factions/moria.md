# Moria

## Identity

Moria is a subterranean fortress and industrial faction defined by durability, tunnel logistics, and relentless endurance.

## Core mechanics

### Mithril Core
Moria maintains metal extraction beyond a normal depletion point, but the system should require a structure or deep mineral infrastructure. It should not create infinite metal with no cost or effort.

Implemented: depleted metal nodes convert to permanent Deep Shafts yielding
at 50% of the normal rate. Worker-presence or upkeep requirements are deferred.

### Tunnels
Tunnel entrances support strategic movement, supply, and defense. Tunnels should be visible, captureable, and vulnerable to blockade or sabotage.

Current implementation: units near tunnel entrances receive +7% movement from
the entrance aura, and a separate Deep Roadways technology grants +5% infantry
movement globally. Restricting the bonus to linked tunnels only remains
deferred.

### Cavalry (none by design)
Khazad-dûm at its zenith navigated tunnels, not plains. Moria builds no Stables and fields no mounted units (per `cavalry_recommendations.md`).

Finalized alternatives:
- Khazad-dûm Mountain Ranger — high-vision foot scout with throwing axes.
- Provisions Cart — slow, sturdy, non-combat mobile drop-site for all resources (reuses the German supply wagon; trainable from the Civic Centre).

### Stone-built structures
Initial balance proposal: for ordinary buildings whose construction is wood-heavy and lore-appropriate as stonework, replace half the Wood cost with Stone while keeping the combined resource cost unchanged. For example, a 150-Wood House becomes 75 Wood + 75 Stone, and a 100-Wood Storehouse becomes 50 Wood + 50 Stone. Leave wood-intensive workshops and siege infrastructure alone, and avoid adding Stone to buildings that already have a substantial Stone cost.

Implemented: the civic/economic halls, vaults, and dwellings now split half
their Wood into Stone at unchanged total cost — House 75W → 38W+37S,
Storehouse 100W → 50W+50S, Farmstead 100W → 50W+50S, Market 300W → 150W+150S.
Left alone per the rule: the Field (a crop plot, not stonework), the Forge and
Siege Hall (wood-intensive workshops / siege infrastructure), and every
building already carrying substantial Stone (Barracks, Civic Centre, Fortress,
Gatewarden Tower, Mithril Deep-Shaft, Tunnel Mouth, Wonder, Temple, walls). The
cheap timber defensive tier (Outpost, Crag Watch sentry tower) is also left as
Wood, matching Moria's "pillared stone + Germanic timber" split
(`design-decisions.md`); revisit if playtests want those stoneworked too.

Do not add a dedicated Stone-mining technology yet. Playtest the building-cost shift first, accounting for Moria's existing Stone-income features; if Stone becomes a sustained bottleneck, consider a modest mining-rate technology.

### Siege (per `siege_recommendations.md`)
Subterranean engineering — no open-air heavy catapults; terrain manipulation and chokepoint breaching instead.
Finalized: elite Sapping Teams (specialized infantry, massive structural damage to walls, weak in open combat); heavy compact Steam-powered Rams built for clearing tight chokepoints and gates. Champion Mithril Vanguard + Náin crush aura supplement, not replace, this toolset.

## Strengths

- heavy infantry and strong durability
- deep underground economy
- defensive chokepoints and fortress play
- excellent late-game stability

## Weaknesses

- slow expansion and movement
- vulnerable to cavalry and attacks that bypass a tunnel choke
- high set-up cost and poor flexibility in open terrain

## Structures

- mines; deep vaults; tunnel entrances; fortress gates; defensive halls; workshop and heavy industrial structures.

Finalized tree (kept): Phase I — CC, House, Storehouse, Mine Shaft, Field, Outpost, Stone Palisade. Phase II — Barracks, Market, Blacksmith, Defensive Bastion, Heavy Stone Wall, Tunnel Entrance. Phase III — Fortress, Temple, Wonder.

## Units

- heavy infantry; durable melee line; tunnel scouts or support units; strong siege support; elite deep-guard units.

Implemented roles include the Miner, durable melee infantry, short-range
throwing-axe skirmishers (no bow archers), Siege Engineer, Steam Ram, Mithril
Vanguard, Mountain Ranger, and Provisions Cart. The cart is a true mobile
drop-site (German supply wagon base).
Moria has no Stables or mounted units.

## Heroes

- deep-guard commander; fortress commander; heroic defender with high health and a local aura.

Finalized (localized only): Durin VI (+20% nearby HP + fear immunity), Náin (+crush vs structures nearby), Fundin (+stone/metal gather nearby).

## Wonder

The wonder embodies Khazad-dûm's unmatched defensive strength: while it stands, Moria's buildings are exceptionally difficult to destroy and very slow to capture, even for a large attacking force. The protection is not invulnerability; a committed assault can still take buildings, but must hold its ground long enough for Moria to respond. Both protections end if the wonder falls.

Implemented: **The Dwarrowdelf** hardens the owner's structures while it
stands — +50% building health (`Health/Max` ×1.5) and capture that takes twice
as long and heals four times as fast once the assault lapses
(`Capturable/CapturePoints` ×2, `Capturable/RegenRate` ×4). It is a player-wide
modifier bundle affecting `Structure !Wonder`, so walls and towers are covered
but the wonder itself stays a normal, killable objective. Foundations, captured
vaults, and defeated owners empower nothing; both protections end the moment the
wonder falls.

Name: **The Dwarrowdelf** — an epithet for Khazad-dûm itself, giving the wonder a name rooted in the legendary Dwarven realm it represents. “Halls of Durin” remains a more building-like alternative if a distinct structure name is preferred.

Shelved concepts: the Great Bridge with near-infinite HP and 50% pass-through speed; cheaper underground infrastructure; tunnel-network reinforcement; speed and healing for units exiting linked entrances; and entrance defense/repair. No map-wide movement buff.

## Counterplay

Cut the tunnel network, bring siege and anti-large pressure, and force Moria into open battle where its wall-heavy strengths are less useful.
