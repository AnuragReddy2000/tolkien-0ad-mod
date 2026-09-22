# Angmar — Detailed Design

## Identity

Angmar is a dark northern realm of cold, fear, sorcery, and temporary necromantic reinforcement. Its battlefield advantage comes from local control and attrition, not from a permanent free army.

## Iron Crown Frost

Enemies engaging Angmar units or structures in close melee suffer a temporary attack-speed reduction, initially around 10% for 3 seconds. The effect should remain local and should not stack uncontrollably with other slows.

## Barrow Plague

When an eligible enemy military unit dies within the aura of an Angmar Temple, Dark Temple, or Witch-Fortress, it has an approximately 15% chance to rise as an Undead Thrall under Angmar’s control.

Suggested eligibility:

- ordinary enemy military unit: 15%;
- champion: 5–10%;
- siege: reduced chance or excluded during initial testing;
- workers: no;
- heroes: no;
- summoned units: no;
- Angmar units: no.

The percentage refers to the share of eligible deaths expected to convert, not a threshold. No artificial faction-wide cap is required. The natural limit is created by the invading force, conversion chance, and Thrall lifetime.

Each death can trigger at most one conversion. Thralls cannot trigger further conversions.

## Undead Thralls

Thralls are weak, temporary, controllable melee auxiliaries:

- roughly 40–50% of ordinary infantry health;
- roughly 50–65% of ordinary infantry attack;
- low armour;
- slightly reduced speed;
- no resource or population cost;
- approximately 45-second TTL with gradual decay.

They can move, attack, patrol, guard, stop, and attack-move. They cannot gather, construct, repair, capture territory, garrison, train units, or create more Thralls.

Full player control is preferred. Automatic-only behavior would make their battlefield value unpredictable and could cause them to waste themselves on unsuitable targets.

## Wonder

The Citadel of Carn Dûm creates a local frost shroud that reduces invading enemy visibility and firing range near the base. It should not become a map-wide suppression mechanic.

## Weaknesses

Angmar is vulnerable to ranged pressure, mobility, economy disruption, and battles fought away from its temple and fortress auras.
