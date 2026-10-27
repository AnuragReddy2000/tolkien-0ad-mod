/**
 * BlightedDesolation — Mordor's territory-wide gather penalty.
 *
 * Enemy workers gathering anywhere inside Mordor-controlled territory (or a
 * small spillover distance beyond its border) suffer -15% gather speed.
 * Gathering only: no build/move/combat effect, no node destruction.
 * Mordor-civ workers are immune; the effect ends when the land is left or
 * reclaimed. Never stacks (one shared modifier key for all sources).
 *
 * Why a component and not a range aura: the design calls for the ENTIRE
 * territory plus a small distance beyond the boundary. Aura radii only
 * approximate this around individual structures, leaving far-flung territory
 * unaffected. This ticker instead asks the TerritoryManager who owns the
 * ground under each enemy worker.
 *
 * Determinism: fixed tick order over a sorted entity list, no RNG, only
 * timer-driven state — lockstep-safe. Application is idempotent, so several
 * Mordor structures ticking over the same territory converge instead of
 * stacking.
 *
 * Verified engine APIs: Timer.SetInterval/GetTime, RangeManager.ExecuteQuery
 * and GetEntitiesByPlayer (cf. EyeOfSauron.js, Auras.js), TerritoryManager
 * GetOwner(x, z) (ICmpTerritoryManager), ModifiersManager AddModifiers /
 * RemoveAllModifiers with DeriveModificationsFromTech (cf. Auras.js),
 * StatusEffectsReceiver AddStatus/RemoveStatus (cf. Visibility.js).
 */
function BlightedDesolation() {}

BlightedDesolation.prototype.Schema =
	"<optional>" +
		"<element name='TickInterval' a:help='Ms between territory sweeps (default 2000).'>" +
			"<data type='nonNegativeInteger'/>" +
		"</element>" +
	"</optional>" +
	"<optional>" +
		"<element name='SpilloverRange' a:help='Meters beyond the territory border still blighted (default 12).'>" +
			"<data type='nonNegativeInteger'/>" +
		"</element>" +
	"</optional>" +
	"<optional>" +
		"<element name='QueryRadius' a:help='Worker-hunt radius around this structure (default 1500, covers large maps).'>" +
			"<data type='nonNegativeInteger'/>" +
		"</element>" +
	"</optional>";

/** Shared modifier key: every source applies the same key so overlap never stacks. */
BlightedDesolation.prototype.ModifierKey = "blighted-desolation";

BlightedDesolation.prototype.StatusCode = "BlightedMordor";

/** -15% gather speed, gathering only. Mirrors data/auras/structures/mordor_blight.json. */
BlightedDesolation.prototype.GetDerivedModifiers = function()
{
	return DeriveModificationsFromTech({
		"modifications": [
			{ "value": "ResourceGatherer/BaseSpeed", "multiply": 0.85 }
		],
		"affects": ["Worker"]
	});
};

BlightedDesolation.prototype.Init = function()
{
	/** Workers this source currently holds blighted (plain array: Sets do not survive save/load serialization). */
	this.blighted = [];

	// SkirmishReplacer can create entities whose ownership fires before real
	// template data exists; bail out and rely on RemoveAll()'s guards.
	if (!this.template)
		return;

	this.tickInterval = this.template.TickInterval ? +this.template.TickInterval : 2000;
	this.spillover = this.template.SpilloverRange ? +this.template.SpilloverRange : 12;
	this.queryRadius = this.template.QueryRadius ? +this.template.QueryRadius : 1500;

	const cmpTimer = Engine.QueryInterface(SYSTEM_ENTITY, IID_Timer);
	cmpTimer.SetInterval(this.entity, IID_BlightedDesolation, "BlightTick", 0, this.tickInterval);
};

/**
 * The blight only flows from a completed structure held by a living Mordor player.
 */
BlightedDesolation.prototype.IsEmpowered = function()
{
	if (Engine.QueryInterface(this.entity, IID_Foundation))
		return false;

	const cmpOwnership = Engine.QueryInterface(this.entity, IID_Ownership);
	if (!cmpOwnership)
		return false;
	const owner = cmpOwnership.GetOwner();
	if (owner == INVALID_PLAYER || owner == 0)
		return false;

	const cmpPlayerManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_PlayerManager);
	const cmpPlayer = Engine.QueryInterface(cmpPlayerManager.GetPlayerByID(owner), IID_Player);
	if (!cmpPlayer || (cmpPlayer.IsDefeated && cmpPlayer.IsDefeated()))
		return false;

	const cmpOwnerIdentity = Engine.QueryInterface(cmpPlayerManager.GetPlayerByID(owner), IID_Identity);
	return !!cmpOwnerIdentity && cmpOwnerIdentity.GetCiv() == "mordor";
};

BlightedDesolation.prototype.GetOwner = function()
{
	return Engine.QueryInterface(this.entity, IID_Ownership).GetOwner();
};

/** Mordor-civ workers are immune to their own shadow (covers mirror matches). */
BlightedDesolation.prototype.IsMordorWorker = function(ent)
{
	const cmpOwnership = Engine.QueryInterface(ent, IID_Ownership);
	if (!cmpOwnership)
		return false;
	const cmpPlayerManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_PlayerManager);
	const cmpIdentity = Engine.QueryInterface(cmpPlayerManager.GetPlayerByID(cmpOwnership.GetOwner()), IID_Identity);
	return !!cmpIdentity && cmpIdentity.GetCiv() == "mordor";
};

/**
 * True while the worker gathers inside `owner`'s territory or within the
 * spillover distance beyond its border (sampled at four cardinal points so
 * only GetOwner — a confirmed script API — is needed).
 */
BlightedDesolation.prototype.IsBlightedGround = function(owner, x, z)
{
	const cmpTerritoryManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_TerritoryManager);
	if (!cmpTerritoryManager)
		return false;

	if (cmpTerritoryManager.GetOwner(x, z) == owner)
		return true;

	const s = this.spillover;
	return cmpTerritoryManager.GetOwner(x + s, z) == owner ||
		cmpTerritoryManager.GetOwner(x - s, z) == owner ||
		cmpTerritoryManager.GetOwner(x, z + s) == owner ||
		cmpTerritoryManager.GetOwner(x, z - s) == owner;
};

BlightedDesolation.prototype.ApplyBlight = function(ent)
{
	if (this.blighted.indexOf(ent) != -1)
		return;
	const cmpModifiersManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_ModifiersManager);
	cmpModifiersManager.AddModifiers(this.ModifierKey, this.GetDerivedModifiers(), ent);
	const cmpReceiver = Engine.QueryInterface(ent, IID_StatusEffectsReceiver);
	if (cmpReceiver)
		cmpReceiver.AddStatus(this.StatusCode, { "Stackability": "Ignore" }, this.entity, this.GetOwner());
	this.blighted.push(ent);
};

BlightedDesolation.prototype.RemoveBlight = function(ent)
{
	const index = this.blighted.indexOf(ent);
	if (index == -1)
		return;
	const cmpModifiersManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_ModifiersManager);
	if (cmpModifiersManager)
		cmpModifiersManager.RemoveAllModifiers(this.ModifierKey, ent);
	// The worker may be gone (killed); guard before touching it.
	if (Engine.QueryInterface(ent, IID_Position))
	{
		const cmpReceiver = Engine.QueryInterface(ent, IID_StatusEffectsReceiver);
		if (cmpReceiver)
			cmpReceiver.RemoveStatus(this.StatusCode);
	}
	this.blighted.splice(index, 1);
};

BlightedDesolation.prototype.RemoveAll = function()
{
	// OnOwnershipChanged can fire before Init in the SkirmishReplacer workflow.
	if (!this.blighted)
		return;
	for (const ent of this.blighted.slice().sort((a, b) => a - b))
		this.RemoveBlight(ent);
};

BlightedDesolation.prototype.FindEnemyWorkers = function(owner)
{
	const cmpPlayerManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_PlayerManager);
	const cmpDiplomacy = Engine.QueryInterface(cmpPlayerManager.GetPlayerByID(owner), IID_Diplomacy);
	if (!cmpDiplomacy)
		return [];

	const enemies = [];
	for (const p of cmpPlayerManager.GetNonGaiaPlayers())
		if (p != owner && cmpDiplomacy.IsEnemy(p))
			enemies.push(p);
	if (!enemies.length)
		return [];

	const cmpRangeManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_RangeManager);
	const candidates = cmpRangeManager.ExecuteQuery(this.entity, 0, this.queryRadius, enemies, IID_UnitAI, false);

	const workers = [];
	for (const ent of candidates)
	{
		const cmpIdentity = Engine.QueryInterface(ent, IID_Identity);
		if (!cmpIdentity || !cmpIdentity.HasClass("Worker") || this.IsMordorWorker(ent))
			continue;
		const cmpPosition = Engine.QueryInterface(ent, IID_Position);
		if (!cmpPosition || !cmpPosition.IsInWorld())
			continue;
		workers.push(ent);
	}
	// Fixed order keeps every lockstep peer converged identically.
	workers.sort((a, b) => a - b);
	return workers;
};

// Note: the timer invokes "BlightTick" (schema-stable name); keep the exact
// spelling the interval was registered with.
BlightedDesolation.prototype.BlightTick = function()
{
	if (!this.IsEmpowered())
	{
		this.RemoveAll();
		return;
	}

	const owner = this.GetOwner();
	const covered = [];
	for (const ent of this.FindEnemyWorkers(owner))
	{
		const pos = Engine.QueryInterface(ent, IID_Position).GetPosition2D();
		if (this.IsBlightedGround(owner, pos.x, pos.y))
		{
			this.ApplyBlight(ent);
			covered.push(ent);
		}
	}
	// Release workers that left the shadow (or were reclaimed) since last tick.
	for (const ent of this.blighted.slice().sort((a, b) => a - b))
		if (covered.indexOf(ent) == -1)
			this.RemoveBlight(ent);
};

BlightedDesolation.prototype.OnDestroy = function()
{
	this.RemoveAll();
};

BlightedDesolation.prototype.OnOwnershipChanged = function()
{
	this.RemoveAll();
};

Engine.RegisterComponentType(IID_BlightedDesolation, "BlightedDesolation", BlightedDesolation);
