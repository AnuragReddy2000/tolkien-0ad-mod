# Doriath

## Identity

Doriath is a hidden woodland faction built around ambushes, concealment, and controlling forested terrain.

## Core mechanics

### Girdle of Melian
Enemy detection and movement are degraded inside Doriath territory. This should be local, readable, and healable through reclaiming territory or clearing forest pressure.

Implemented as a structure-projected movement/vision effect. Keep its strength around structures; do not scale it by forest density or weaken it on open ground. Counterplay includes scouting, detection, area attacks, and removing the projecting structure. Strict un-scoutable fog is not part of the current design.

### Forest Camouflage and Woodland Bonuses
Stationary forest camouflage is implemented for selected units. The woodland movement bonus (Scout, Hunter, Ranger, March-warden move +10% in forest) and the Guard of the Caves' forest-only armour (base 3/3/13, +2 Hack/Pierce/Crush in forest) are live through the `ForestAffinity` component, which reads tree density around the unit. When a concealed Ranger receives an attack order against a target that has not detected it, its next ranged attack launched gets +50% damage; the bonus is consumed on launch, even if the projectile misses. Moving, taking damage, or replacing the attack order before launch cancels the bonus. In-game validation remains pending.

### Guardianship of the Greenwood
Implemented as a Town-phase technology at the Storehouse. After researching it,
Doriath gatherers leave at least 5% of a tree's maximum wood supply standing.
Other factions can still gather the remaining wood.

### Cavalry (none by design)
The Sindar fought entirely on foot. Doriath builds no Stables and fields no mounted units (per `cavalry_recommendations.md`).

Finalized alternatives:
- Sindarin Green-weave Scout — fast foot scout with passive Forest Camouflage (invisible near trees) and a large bonus vs wild game; replaces the starting horse scout.
- Hunter's Cache — implemented, low-cost food-only forward dropsite for gathering near wildlife. It costs 50 Wood and 10 Stone and takes 20 seconds to build; it supports foraging logistics, not military mobility or cavalry roles.

### Menegroth
Menegroth deepens the Girdle and supports the faction's territorial defense. It should not create arbitrary production penalties or permanent unscoutable map control.

Implemented — "The Girdle Deepens": Menegroth adds a stronger structure-projected Girdle effect while standing. Keep the effect tied to projecting structures; do not scale it by forest density or limit it to hidden forest units. No global production effect.

## Strengths

- stealth and ambush play
- woodland defense and concealment
- strong in forests and prepared terrain
- strong sabotage and harassment potential

## Weaknesses

- weak in open ground and set-piece direct combat
- fragile if discovered and forced into melee
- dependent on terrain and map layout

## Structures

- woodland encampments; forest watch sites; hidden safehouses; ambush structures; fortified halls; core production structures with concealment support.

Finalized tree (kept): Phase I — CC, House, Storehouse, Farmstead, Field, Enchanted Outpost. Phase II — Barracks, Market, Blacksmith, Mounded Watchtower, Stone Wall (weaker than Gondor/Moria). Phase III — Fortress, Temple, Menegroth. Enchanted Outpost: pricier, +forest vision, extends mist, conceals nearby stationary friendlies (info role, not tower). Mounded Watchtower: high LOS in forest, small garrison.

## Units

- concealed scouts; ambush infantry; long-range skirmishers; elite woodland defenders; elite ranged support.

Implemented roles: Laiquendi Skirmisher (stealth javelin), Sindar Axeman (basic axe infantry without anti-cavalry bonus), March-warden (stealth bow champion), Guard of the Caves (dual axes, no shield), Saboteur (structure demolition; cannot attack units), and Ent-ally (organic siege). The Green-weave Scout is a fast foot scout with forest camouflage and an animal bonus. No Stables or mounted units.

### Siege — none mechanical (per `siege_recommendations.md`)
Hidden kingdom that never marches outward to besiege — no mechanical siege, stealth + environmental manipulation instead.
Finalized: Elven Saboteurs approach enemy buildings camouflaged to plant destructive charges; rare Ent-allies / Huorns serve as organic siege champions for walls.

## Heroes

- a ranger or hidden commander; a forest guardian hero; a hero with local concealment, morale support, or ambush damage bonuses.

Melian, Thingol, and Beleg are implemented heroes. Their current combat profiles and aura effects should be read from their templates; proposed forest movement, accuracy, and attack-speed effects that are absent from those templates are not live bonuses.

## Wonder

The wonder should emphasize concealment and territory control. It should not completely negate all enemy scouting or make the map permanently invisible.

## Counterplay

Use cavalry, fire, siege, and broad territory control to disrupt the Girdle. Avoid fighting in the forest if the faction has already prepared the terrain.

## Balance notes

Stealth should be tactical, not universal. Doriath's concern is misdirection and preparation, not permanent enemy blindness.
