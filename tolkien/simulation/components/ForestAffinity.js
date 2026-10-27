/**
 * ForestAffinity — Doriath's terrain-conditioned combat bonuses.
 *
 * A unit carrying this component gains a self-applied modifier bundle while it
 * stands in forest, and loses it the moment it leaves. The bundle is declared
 * per-unit in the template's <Modifiers> block (the XML is the balance source
 * of truth), so the same component powers both the woodland movement bonus and
 * the Guard of the Caves' forest-only armour.
 *
 * "Forest" is defined exactly as the camouflage does it: enough wood-yielding
 * ResourceSupply (trees) within a radius. There is no terrain-class concept in
 * the engine, so tree density is the only deterministic forest signal.
 *
 * Why a component and not an aura: auras project from a source onto other
 * entities by class/range. This is the unit reading its own footing, so the
 * modifiers are applied to self with an empty affects list (cf.
 * DoesModificationApply — empty affects always applies).
 *
 * Determinism: timer-driven state only, fixed ResourceSupply query, no RNG.
 * Application is idempotent (guarded by HasAnyModifier), so re-entry, save/load
 * and overlapping ticks converge instead of stacking.
 *
 * Verified engine APIs: Timer.SetInterval/GetTime, RangeManager.ExecuteQuery,
 * ResourceSupply.GetType, ModifiersManager AddModifiers/RemoveAllModifiers/
 * HasAnyModifier with DeriveModificationsFromXMLTemplate (cf. BlightedDesolation.js,
 * StatusEffectsReceiver.js), StatusEffectsReceiver AddStatus/RemoveStatus.
 */
function ForestAffinity() {}

ForestAffinity.prototype.Schema =
	"<interleave>" +
	"<optional>" +
		"<element name='ForestRadius' a:help='Meters to scan for trees (default 10, matches camouflage).'>" +
			"<data type='positiveInteger'/>" +
		"</element>" +
	"</optional>" +
	"<optional>" +
		"<element name='MinTrees' a:help='Wood-yielding resources needed to count as forest (default 4).'>" +
			"<data type='positiveInteger'/>" +
		"</element>" +
	"</optional>" +
	"<optional>" +
		"<element name='TickInterval' a:help='Ms between forest checks (default 500).'>" +
			"<data type='positiveInteger'/>" +
		"</element>" +
	"</optional>" +
	"<optional>" +
		"<element name='StatusCode' a:help='Optional status-effect code toggled for the UI icon/tooltip while in forest.'>" +
			"<text/>" +
		"</element>" +
	"</optional>" +
	"<element name='Modifiers' a:help='Modifier bundle applied to this unit while it stands in forest.'>" +
		"<oneOrMore>" +
			"<element>" +
				"<anyName/>" +
				"<interleave>" +
					"<element name='Paths' a:help='Space separated value paths to modify.'>" +
						"<attribute name='datatype'>" +
							"<value>tokens</value>" +
						"</attribute>" +
						"<text/>" +
					"</element>" +
					"<optional>" +
						"<element name='Affects' a:help='Optional extra class filter (omit to affect only this unit).'>" +
							"<attribute name='datatype'>" +
								"<value>tokens</value>" +
							"</attribute>" +
							"<text/>" +
						"</element>" +
					"</optional>" +
					"<choice>" +
						"<element name='Add'><data type='decimal'/></element>" +
						"<element name='Multiply'><data type='decimal'/></element>" +
						"<element name='Replace'><text/></element>" +
					"</choice>" +
				"</interleave>" +
			"</element>" +
		"</oneOrMore>" +
	"</element>" +
	"</interleave>";

/** Shared modifier key: one key per entity, so add/remove never stacks. */
ForestAffinity.prototype.ModifierKey = "forest-affinity";

ForestAffinity.prototype.Init = function()
{
	this.inForest = false;

	// SkirmishReplacer can create entities before real template data exists.
	if (!this.template || !this.template.Modifiers)
		return;

	this.forestRadius = this.template.ForestRadius ? +this.template.ForestRadius : 10;
	this.minTrees = this.template.MinTrees ? +this.template.MinTrees : 4;
	this.tickInterval = this.template.TickInterval ? +this.template.TickInterval : 500;
	this.statusCode = this.template.StatusCode || null;

	const cmpTimer = Engine.QueryInterface(SYSTEM_ENTITY, IID_Timer);
	cmpTimer.SetInterval(this.entity, IID_ForestAffinity, "ForestTick", this.tickInterval, this.tickInterval);
};

ForestAffinity.prototype.GetModifiers = function()
{
	return DeriveModificationsFromXMLTemplate(this.template.Modifiers);
};

ForestAffinity.prototype.IsInForest = function()
{
	const cmpRangeManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_RangeManager);
	const trees = cmpRangeManager.ExecuteQuery(this.entity, 0, this.forestRadius, [0], IID_ResourceSupply, true);

	let count = 0;
	for (const tree of trees)
	{
		const cmpSupply = Engine.QueryInterface(tree, IID_ResourceSupply);
		if (cmpSupply && cmpSupply.GetType().generic == "wood" && ++count >= this.minTrees)
			return true;
	}
	return false;
};

ForestAffinity.prototype.EnterForest = function()
{
	if (this.inForest)
		return;
	this.inForest = true;

	const cmpModifiersManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_ModifiersManager);
	if (!cmpModifiersManager.HasAnyModifier(this.ModifierKey, this.entity))
		cmpModifiersManager.AddModifiers(this.ModifierKey, this.GetModifiers(), this.entity);

	if (this.statusCode)
	{
		const cmpReceiver = Engine.QueryInterface(this.entity, IID_StatusEffectsReceiver);
		if (cmpReceiver)
			cmpReceiver.AddStatus(this.statusCode, { "Stackability": "Ignore" }, INVALID_ENTITY, INVALID_PLAYER);
	}
};

ForestAffinity.prototype.LeaveForest = function()
{
	if (!this.inForest)
		return;
	this.inForest = false;

	const cmpModifiersManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_ModifiersManager);
	if (cmpModifiersManager)
		cmpModifiersManager.RemoveAllModifiers(this.ModifierKey, this.entity);

	if (this.statusCode && Engine.QueryInterface(this.entity, IID_StatusEffectsReceiver))
	{
		const cmpReceiver = Engine.QueryInterface(this.entity, IID_StatusEffectsReceiver);
		cmpReceiver.RemoveStatus(this.statusCode);
	}
};

ForestAffinity.prototype.ForestTick = function()
{
	if (!this.template || !this.template.Modifiers)
		return;

	const cmpPosition = Engine.QueryInterface(this.entity, IID_Position);
	if (!cmpPosition || !cmpPosition.IsInWorld())
	{
		this.LeaveForest();
		return;
	}

	if (this.IsInForest())
		this.EnterForest();
	else
		this.LeaveForest();
};

ForestAffinity.prototype.OnDestroy = function()
{
	const cmpModifiersManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_ModifiersManager);
	if (cmpModifiersManager)
		cmpModifiersManager.RemoveAllModifiers(this.ModifierKey, this.entity);
};

Engine.RegisterComponentType(IID_ForestAffinity, "ForestAffinity", ForestAffinity);