const VIS_HIDDEN = 0;
const VIS_FOGGED = 1;
const VIS_VISIBLE = 2;

function Visibility() {}

Visibility.prototype.Schema =
	"<element name='RetainInFog'>" +
		"<data type='boolean'/>" +
	"</element>" +
	"<element name='AlwaysVisible'>" +
		"<data type='boolean'/>" +
	"</element>" +
	"<element name='Corpse'>" +
		"<data type='boolean'/>" +
	"</element>" +
	"<element name='Preview'>" +
		"<data type='boolean'/>" +
	"</element>" +
	"<optional>" +
		"<element name='Camouflage' a:help='Conditional forest camouflage (Doriath). Optional parameters with defaults.'>" +
			"<interleave>" +
				"<optional><element name='StationaryDelay'><data type='nonNegativeInteger'/></element></optional>" +
				"<optional><element name='ForestRadius'><data type='positiveInteger'/></element></optional>" +
				"<optional><element name='MinTrees'><data type='positiveInteger'/></element></optional>" +
				"<optional><element name='DetectRadius'><data type='positiveInteger'/></element></optional>" +
				"<optional><element name='GirdleDetectRadius' a:help='Detection radius used instead of DetectRadius while the concealed unit stands inside a friendly Girdle of Melian aura (structure class Girdle).'><data type='positiveInteger'/></element></optional>" +
			"</interleave>" +
		"</element>" +
	"</optional>";

Visibility.prototype.Init = function()
{
	this.retainInFog = this.template.RetainInFog == "true";
	this.alwaysVisible = this.template.AlwaysVisible == "true";
	this.corpse = this.template.Corpse == "true";
	this.preview = this.template.Preview == "true";

	this.activated = false;

	if (this.preview || this.corpse)
		this.SetActivated(true);

	// === Tolkien mod: conditional camouflage (Doriath) ===
	// Gated entirely by the presence of a <Camouflage> block in this
	// component's template. Entities without it are completely unaffected:
	// no timer, no scripted visibility, vanilla behaviour only.
	this.camouflage = null;
	this.concealed = false;
	this.revealedTo = new Set();
	this.lastMoveTime = 0;
	this.camouflageTimer = null;

	if (this.template.Camouflage)
	{
		const c = this.template.Camouflage;
		this.camouflage = {
			"stationaryDelay": +(c.StationaryDelay || 3000),
			"forestRadius": +(c.ForestRadius || 10),
			"minTrees": +(c.MinTrees || 4),
			"detectRadius": +(c.DetectRadius || 12),
			"girdleDetectRadius": c.GirdleDetectRadius ? +c.GirdleDetectRadius : null
		};
		const cmpTimer = Engine.QueryInterface(SYSTEM_ENTITY, IID_Timer);
		this.camouflageTimer = cmpTimer.SetInterval(this.entity, IID_Visibility, "UpdateCamouflage", 1000, 500);
	}
};

/**
 * Sets the range manager scriptedVisibility flag for this entity.
 */
Visibility.prototype.SetActivated = function(status)
{
	const cmpRangeManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_RangeManager);
	cmpRangeManager.ActivateScriptedVisibility(this.entity, status);

	this.activated = status;
};

/**
 * This function is a fallback for some entities whose visibility status
 * cannot be cached by the range manager (especially local entities like previews).
 * Calling the scripts is expensive, so only call it if really needed.
 */
Visibility.prototype.IsActivated = function()
{
	return this.activated;
};

/**
 * This function is called if the range manager scriptedVisibility flag is set to true for this entity.
 * If so, the return value supersedes the visibility computed by the range manager.
 * isVisible: true if the entity is in the vision range of a unit, false otherwise
 * isExplored: true if the entity is in explored territory, false otherwise
 */
Visibility.prototype.GetVisibility = function(player, isVisible, isExplored)
{
	if (this.preview)
	{
		// For the owner only, mock the "RetainInFog" behavior
		const cmpOwnership = Engine.QueryInterface(this.entity, IID_Ownership);
		if (cmpOwnership && cmpOwnership.GetOwner() == player && isExplored)
			return isVisible ? VIS_VISIBLE : VIS_FOGGED;

		// For others, hide the preview
		return VIS_HIDDEN;
	}
	else if (this.corpse)
	{
		// For the owner only, mock the "RetainInFog" behavior
		const cmpOwnership = Engine.QueryInterface(this.entity, IID_Ownership);
		if (cmpOwnership && cmpOwnership.GetOwner() == player && isExplored)
			return isVisible ? VIS_VISIBLE : VIS_FOGGED;

		// For others, regular displaying
		return isVisible ? VIS_VISIBLE : VIS_HIDDEN;
	}

	// === Tolkien mod: conditional camouflage ===
	// Vanilla never reaches this tail with scripted visibility active on a
	// normal unit, so compute the range-manager equivalent explicitly.
	const normal = isVisible ? VIS_VISIBLE : (isExplored ? VIS_FOGGED : VIS_HIDDEN);

	if (this.concealed)
	{
		const cmpOwnership = Engine.QueryInterface(this.entity, IID_Ownership);
		const owner = cmpOwnership ? cmpOwnership.GetOwner() : INVALID_PLAYER;

		if (owner != player && !this.revealedTo.has(player))
		{
			const cmpPlayerManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_PlayerManager);
			const cmpViewer = Engine.QueryInterface(cmpPlayerManager.GetPlayerByID(player), IID_Diplomacy);

			// Mutual allies always perceive normally. Enemies only get the
			// last-known (fogged) position, never the live one.
			if (!(cmpViewer && cmpViewer.IsMutualAlly(owner)))
				return isExplored ? VIS_FOGGED : VIS_HIDDEN;
		}
	}

	return normal;
};

Visibility.prototype.GetRetainInFog = function()
{
	return this.retainInFog;
};

Visibility.prototype.GetAlwaysVisible = function()
{
	return this.alwaysVisible;
};

// === Tolkien mod: camouflage state machine ===
// Only ever runs for entities whose template declared <Camouflage>.

Visibility.prototype.IsConcealed = function()
{
	return this.concealed;
};

Visibility.prototype.SetConcealed = function(state)
{
	if (this.concealed == state)
		return;

	this.concealed = state;
	// Scripted visibility is only active while concealed: zero overhead
	// for every other entity in the game.
	this.SetActivated(state);

	const cmpReceiver = Engine.QueryInterface(this.entity, IID_StatusEffectsReceiver);
	if (cmpReceiver)
	{
		if (state)
			cmpReceiver.AddStatus("ConcealedDoriath", { "Stackability": "Ignore" }, INVALID_ENTITY, INVALID_PLAYER);
		else
			cmpReceiver.RemoveStatus("ConcealedDoriath");
	}
};

Visibility.prototype.BreakCamouflage = function(reason)
{
	if (!this.camouflage || !this.concealed)
		return;

	this.SetConcealed(false);
};

Visibility.prototype.IsInForest = function()
{
	const cmpRangeManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_RangeManager);
	const trees = cmpRangeManager.ExecuteQuery(this.entity, 0, this.camouflage.forestRadius, [0], IID_ResourceSupply, true);

	let count = 0;
	for (const tree of trees)
	{
		const cmpSupply = Engine.QueryInterface(tree, IID_ResourceSupply);
		if (cmpSupply && cmpSupply.GetType().generic == "wood" && ++count >= this.camouflage.minTrees)
			return true;
	}
	return false;
};

/**
 * True while this entity stands inside a friendly Girdle of Melian aura
 * (any owned structure carrying the "Girdle" class whose range aura covers
 * us). Deterministic: fixed query order, no RNG.
 */
Visibility.prototype.IsInFriendlyGirdle = function()
{
	const cmpOwnership = Engine.QueryInterface(this.entity, IID_Ownership);
	const owner = cmpOwnership ? cmpOwnership.GetOwner() : INVALID_PLAYER;
	if (owner == INVALID_PLAYER)
		return false;

	const cmpPosition = Engine.QueryInterface(this.entity, IID_Position);
	if (!cmpPosition || !cmpPosition.IsInWorld())
		return false;
	const pos = cmpPosition.GetPosition2D();

	const cmpRangeManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_RangeManager);
	// 75 covers the largest Girdle aura radius plus margin.
	const candidates = cmpRangeManager.ExecuteQuery(this.entity, 0, 75, [owner], IID_Auras, true);

	for (const ent of candidates)
	{
		const cmpIdentity = Engine.QueryInterface(ent, IID_Identity);
		// HasClass only reads Classes; the Girdle tag lives in VisibleClasses.
		if (!cmpIdentity || cmpIdentity.GetVisibleClassesList().indexOf("Girdle") == -1 && !cmpIdentity.HasClass("Girdle"))
			continue;

		const cmpEntPosition = Engine.QueryInterface(ent, IID_Position);
		if (!cmpEntPosition || !cmpEntPosition.IsInWorld())
			continue;
		const entPos = cmpEntPosition.GetPosition2D();

		const distSq = (entPos.x - pos.x) * (entPos.x - pos.x) + (entPos.y - pos.y) * (entPos.y - pos.y);

		const cmpAuras = Engine.QueryInterface(ent, IID_Auras);
		for (const name of cmpAuras.GetAuraNames())
		{
			const range = cmpAuras.GetRange(name);
			if (range && distSq <= range * range)
				return true;
		}
	}
	return false;
};

Visibility.prototype.UpdateRevealedTo = function()
{
	const cmpOwnership = Engine.QueryInterface(this.entity, IID_Ownership);
	const owner = cmpOwnership ? cmpOwnership.GetOwner() : INVALID_PLAYER;
	const cmpPlayerManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_PlayerManager);
	const cmpRangeManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_RangeManager);
	const revealed = new Set();

	// Inside the Girdle of Melian, concealed units are only revealed at
	// close range.
	const detectRadius = this.camouflage.girdleDetectRadius && this.IsInFriendlyGirdle() ?
		this.camouflage.girdleDetectRadius :
		this.camouflage.detectRadius;

	for (const player of cmpPlayerManager.GetNonGaiaPlayers())
	{
		if (player == owner)
			continue;

		const cmpDiplomacy = Engine.QueryInterface(cmpPlayerManager.GetPlayerByID(player), IID_Diplomacy);
		if (cmpDiplomacy && cmpDiplomacy.IsMutualAlly(owner))
			continue;

		// Any enemy unit or structure within the detection radius spots us.
		const spotters =
			cmpRangeManager.ExecuteQuery(this.entity, 0, detectRadius, [player], IID_UnitAI, true).length +
			cmpRangeManager.ExecuteQuery(this.entity, 0, detectRadius, [player], IID_BuildingAI, true).length;

		if (spotters)
			revealed.add(player);
	}

	this.revealedTo = revealed;
};

Visibility.prototype.UpdateCamouflage = function()
{
	if (!this.camouflage)
		return;

	const cmpPosition = Engine.QueryInterface(this.entity, IID_Position);
	if (!cmpPosition || !cmpPosition.IsInWorld())
		return;

	const now = Engine.QueryInterface(SYSTEM_ENTITY, IID_Timer).GetTime();
	const stationary = now - this.lastMoveTime >= this.camouflage.stationaryDelay;

	this.UpdateRevealedTo();

	if (this.concealed)
	{
		// Concealment is continuously re-checked: leaving the forest, being
		// shoved out of position, or being spotted by a passer-by ends it.
		if (!stationary || !this.IsInForest())
			this.BreakCamouflage(stationary ? "invalid terrain" : "movement");
		return;
	}

	if (stationary && this.IsInForest())
		this.SetConcealed(true);
};

Visibility.prototype.OnPositionChanged = function(msg)
{
	if (!this.camouflage)
		return;

	const cmpAmbush = Engine.QueryInterface(this.entity, IID_RangerAmbush);
	if (cmpAmbush)
		cmpAmbush.Clear();

	// Any real movement breaks concealment and restarts the stationary timer.
	this.lastMoveTime = Engine.QueryInterface(SYSTEM_ENTITY, IID_Timer).GetTime();
	this.BreakCamouflage("movement");
};

Visibility.prototype.OnAttacked = function(msg)
{
	const cmpAmbush = Engine.QueryInterface(this.entity, IID_RangerAmbush);
	if (cmpAmbush)
		cmpAmbush.Clear();

	// Taking damage (including splash/fire) breaks concealment.
	this.BreakCamouflage("damage");
};

Visibility.prototype.OnUnitAIOrderDataChanged = function(msg)
{
	const cmpAmbush = Engine.QueryInterface(this.entity, IID_RangerAmbush);
	const order = msg.to && msg.to.type;
	if (cmpAmbush)
	{
		const target = msg.to && msg.to.data && msg.to.data.target;
		const cmpTargetOwnership = target != undefined ?
			Engine.QueryInterface(target, IID_Ownership) :
			null;
		const targetOwner = cmpTargetOwnership ? cmpTargetOwnership.GetOwner() : INVALID_PLAYER;
		if (order == "Attack" && this.concealed &&
		    targetOwner != INVALID_PLAYER && !this.revealedTo.has(targetOwner))
			cmpAmbush.Arm();
		else
			cmpAmbush.Clear();
	}

	if (!this.camouflage || !this.concealed)
		return;

	// Attacking or constructing breaks concealment.
	if (order == "Attack" || order == "Build")
		this.BreakCamouflage(order == "Attack" ? "attack" : "construction");
};

Engine.RegisterComponentType(IID_Visibility, "Visibility", Visibility);
