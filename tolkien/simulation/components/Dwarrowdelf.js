/**
 * Dwarrowdelf — The Dwarrowdelf (Moria wonder).
 *
 * While a completed Dwarrowdelf stands in Moria hands, every structure its
 * owner holds is hardened: +50% maximum health, capture points that take twice
 * as long to drain and regenerate four times as fast once the assault lapses.
 * The protection is not invulnerability — a committed attack can still take a
 * building, but it must hold the ground long enough for Khazad-dûm to respond.
 * Both protections end the moment the wonder falls.
 *
 * Design constraints (deliberate):
 * - Structures only, and never the wonder itself: the bundle affects
 *   "Structure !Wonder", so walls and towers are hardened while the wonder
 *   stays a normal, killable objective (raze it to lift the blessing).
 * - Player-wide modifiers, not per-building ticks: the bundle is applied once
 *   to the owner's player entity exactly like a technology, so existing,
 *   future, and recaptured structures are covered automatically and ownership
 *   changes re-resolve the bonus for free (cf. moria_khazad_forging.json, which
 *   buffs Health/Max with affects "Structure", and blessing_of_the_west.json
 *   for the "Class !Class" negation form).
 * - Lives and dies with the wonder: foundations, captured, gaia-held, or
 *   defeated-owner vaults empower nothing.
 *
 * Engine note (0.28): Health/Max and Capturable/{CapturePoints,RegenRate} are
 * modification-aware and rescale current values on MT_ValueModification
 * (Health.RecalculateValues, Capturable.UpdateCachedValuesAndNotify), so the
 * buff and its removal preserve each building's current HP / capture ratio.
 *
 * Determinism: timer-driven state only, idempotent apply (HasAnyModifier
 * guard), no RNG, no unordered iteration — lockstep-safe.
 *
 * Verified engine APIs: Timer.SetInterval, ModifiersManager AddModifiers /
 * RemoveAllModifiers / HasAnyModifier with DeriveModificationsFromTech
 * (cf. BlightedDesolation.js), Identity GetCiv (cf. EyeOfSauron.js).
 */
function Dwarrowdelf() {}

Dwarrowdelf.prototype.Schema =
	"<optional>" +
		"<element name='TickInterval' a:help='Ms between empowerment checks (default 1000).'>" +
			"<data type='nonNegativeInteger'/>" +
		"</element>" +
	"</optional>" +
	"<optional>" +
		"<element name='HealthMultiply' a:help='Multiplier on owned structure max health (default 1.5).'>" +
			"<data type='decimal'/>" +
		"</element>" +
	"</optional>" +
	"<optional>" +
		"<element name='CapturePointsMultiply' a:help='Multiplier on owned structure capture points (default 2).'>" +
			"<data type='decimal'/>" +
		"</element>" +
	"</optional>" +
	"<optional>" +
		"<element name='CaptureRegenMultiply' a:help='Multiplier on owned structure capture regen rate (default 4).'>" +
			"<data type='decimal'/>" +
		"</element>" +
	"</optional>";

/** Shared modifier key: one bundle per owner, so re-entry never stacks. */
Dwarrowdelf.prototype.ModifierKey = "dwarrowdelf";

/** Hardened: every owned structure, but never the wonder itself. */
Dwarrowdelf.prototype.Affects = "Structure !Wonder";

Dwarrowdelf.prototype.Init = function()
{
	this.appliedPlayer = INVALID_ENTITY;

	// SkirmishReplacer can create entities before real template data exists.
	if (!this.template)
		return;

	this.healthMult = this.template.HealthMultiply ? +this.template.HealthMultiply : 1.5;
	this.capMult = this.template.CapturePointsMultiply ? +this.template.CapturePointsMultiply : 2;
	this.regenMult = this.template.CaptureRegenMultiply ? +this.template.CaptureRegenMultiply : 4;
	this.tickInterval = this.template.TickInterval ? +this.template.TickInterval : 1000;

	const cmpTimer = Engine.QueryInterface(SYSTEM_ENTITY, IID_Timer);
	cmpTimer.SetInterval(this.entity, IID_Dwarrowdelf, "DwarrowdelfTick", this.tickInterval, this.tickInterval);
};

Dwarrowdelf.prototype.GetDerivedModifiers = function()
{
	return DeriveModificationsFromTech({
		"modifications": [
			{ "value": "Health/Max", "multiply": this.healthMult, "affects": this.Affects },
			{ "value": "Capturable/CapturePoints", "multiply": this.capMult, "affects": this.Affects },
			{ "value": "Capturable/RegenRate", "multiply": this.regenMult, "affects": this.Affects }
		]
	});
};

/**
 * The vaults harden their holds only when a completed Dwarrowdelf is held by a
 * living Moria player. Foundations (under construction), captured or gaia-held
 * vaults empower nothing.
 */
Dwarrowdelf.prototype.IsEmpowered = function()
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
	return !!cmpOwnerIdentity && cmpOwnerIdentity.GetCiv() == "moria";
};

Dwarrowdelf.prototype.GetOwnerPlayerEntity = function()
{
	const cmpOwnership = Engine.QueryInterface(this.entity, IID_Ownership);
	if (!cmpOwnership)
		return INVALID_ENTITY;
	const owner = cmpOwnership.GetOwner();
	if (owner == INVALID_PLAYER || owner == 0)
		return INVALID_ENTITY;
	return Engine.QueryInterface(SYSTEM_ENTITY, IID_PlayerManager).GetPlayerByID(owner);
};

/**
 * Make the world match the wonder's state: hold the bundle on the owner's
 * player entity while empowered, withdraw it otherwise. Idempotent, so the
 * timer, ownership changes and save/load all converge.
 */
Dwarrowdelf.prototype.Reconcile = function()
{
	// OnOwnershipChanged can fire before Init in the SkirmishReplacer workflow.
	if (this.appliedPlayer === undefined)
		return;

	const desired = this.IsEmpowered() ? this.GetOwnerPlayerEntity() : INVALID_ENTITY;
	if (desired === this.appliedPlayer)
		return;

	const cmpModifiersManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_ModifiersManager);
	if (!cmpModifiersManager)
		return;

	if (this.appliedPlayer != INVALID_ENTITY)
		cmpModifiersManager.RemoveAllModifiers(this.ModifierKey, this.appliedPlayer);

	this.appliedPlayer = INVALID_ENTITY;

	if (desired != INVALID_ENTITY)
	{
		// Survives save/load: the bundle may already sit on the player entity
		// (ModifiersManager serializes it), so adopt rather than re-add.
		if (!cmpModifiersManager.HasAnyModifier(this.ModifierKey, desired))
			cmpModifiersManager.AddModifiers(this.ModifierKey, this.GetDerivedModifiers(), desired);
		this.appliedPlayer = desired;
	}
};

Dwarrowdelf.prototype.DwarrowdelfTick = function()
{
	if (!this.template)
		return;
	this.Reconcile();
};

Dwarrowdelf.prototype.OnOwnershipChanged = function()
{
	this.Reconcile();
};

Dwarrowdelf.prototype.OnDestroy = function()
{
	if (this.appliedPlayer === undefined || this.appliedPlayer == INVALID_ENTITY)
		return;
	const cmpModifiersManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_ModifiersManager);
	if (cmpModifiersManager)
		cmpModifiersManager.RemoveAllModifiers(this.ModifierKey, this.appliedPlayer);
	this.appliedPlayer = INVALID_ENTITY;
};

Engine.RegisterComponentType(IID_Dwarrowdelf, "Dwarrowdelf", Dwarrowdelf);