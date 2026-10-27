# Númenor

## Identity

Númenor is a disciplined elite kingdom that combines strong infrastructure, coastal power, and high-quality military units.

## Core mechanics

### Great Houses and population efficiency
The faction receives modest population support and efficient housing without becoming a universal population machine. The key is quality and infrastructure, not sheer volume.

Implemented bonuses: Houses provide +10% population; non-hero infantry receive +5% health. Earlier proposals for flat 15–16-pop Houses and a terrain-conditioned defensive bonus are not implemented and are not current balance targets.

### Cavalry (restricted)
The Númenóreans bred fine horses but used them for transport, scouting, and messaging — never shock combat (*Unfinished Tales*, per `cavalry_recommendations.md`).

Implemented: Númenórean Scout is a fast, high-vision light cavalry spearman
with a 2.5x bonus against cavalry. Númenor has no shock or champion cavalry.

### Coastal fortification
Fortified docks and coastal infrastructure support naval power and strong coastal defense.

Finalized — Sea-Craft Citadel: higher-HP docks with modest attack, limited coastal territory, limited garrison, stronger Phase II/III upgrades. Fortress-equivalent docks shelved. Implemented: Fortified Havens Dock Health x1.15.

### Siege (per `siege_recommendations.md`)
Peak Númenórean invasion power — siege concentrated at sea, precision engines on land.
Finalized: Heavy Siege Ships with onboard ballistas to dominate shorelines (pairs with War Galley / Juggernaut Warship line + Ar-Pharazôn naval aura); on land masterfully engineered Steel-Bow Ballistas with greater range and projectile velocity than standard wooden variants (pairs with Steel-bow Archer champion line).

## Strengths

- healthy and elite infantry
- strong infrastructure and defensive preparation
- naval and coastal power
- disciplined, expensive army with reliable composition

## Weaknesses

- slow expansion and less mass than cheaper factions
- expensive replacements
- vulnerable to economic disruption and sustained attrition

## Structures

- fortified docks; elite barracks; stone strongholds; urban centers; naval and defence infrastructure.

Finalized tree (kept): Phase I — CC, House, Storehouse, Farmstead, Field, Outpost, Dock, Scout Stables (scouts only, no upgrades). Phase II — Barracks, Market, Blacksmith, Coast Guard Tower (anti-ship/landing specialist, not all-round best), Stone Wall. Phase III — Citadel (Fortress), Temple, Temple of Armenelos.

## Units

- elite infantry; disciplined archers; well-equipped naval units; strong defenders; elite command units.

Finalized: Mariner (basic swordsman, better armor/HP, higher Food+Metal, slower train), Bowman (standard — elite identity lives in champion), Champion Steel-bow Archer (long range, heavy pierce, high HP, expensive Metal, slow train, weak cav/melee/siege), War Galley + Juggernaut Warship Phase III (heavy, slow, strong vs ships/coastal structures, weak focus-fire/fireships/maneuver). Númenórean Scout (Phase I light cav spearman, scouting only); no heavy or champion cavalry.

## Heroes

- a strategic commander; a marine or command hero; a support hero with morale or elite support.

Finalized (localized): Elendil (~+10% nearby attack + LOS + morale resist), Isildur (modest nearby melee + small finishing-strike crit vs wounded/heroes; flat +10% double-damage crit shelved), Ar-Pharazôn (warships +15% attack and +10% health; while alive, Númenórean land-unit Metal costs +10% and maximum population +10%). The population bonus is multiplicative with other cap bonuses (for example, 330 becomes 363); no land-training slowdown. Implemented via the Great Armament aura (player aura: `Player/MaxPopulation` ×1.1 plus a global-style `Cost/Resources/metal` ×1.1 on Númenórean land units; removed when he dies).

## Wonder

The wonder should provide a focused champion, morale, or supreme defensive support effect rather than a broad all-unit buff.

Finalized — Temple of Armenelos: champions +10% health globally (no damage), plus small morale/defensive aura near CCs/Citadels/Docks. Map-wide +10% health + damage (v1) shelved.

## Counterplay

Disrupt coastal supply, force Númenor into attritional fights, and attack production before elite units are fully established.
