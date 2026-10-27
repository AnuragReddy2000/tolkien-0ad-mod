/**
 * LastShore — Arches of the Last Shore (Lindon wonder).
 *
 * While a completed Arches stands in Lindon hands, a share of every fallen
 * Lindon unit's cost returns to the owner's treasury: their spirits reached
 * the West, so the loss is not total. Tuned to soften attrition (Lindon's
 * designed weakness), never erase it.
 *
 * Design constraints (deliberate):
 * - Units only: structures, foundations, heroes, and the wonder itself
 *   never refund. Refunding buildings would pay the player for losing ground.
 * - Flat share of the victim's Cost (default 15%), floored per resource.
 *   Heroes excluded: refunding 150f/300m hero costs would warp hero trades.
 * - Lives and dies with the wonder: foundations, captured, gaia-held, or
 *   defeated-owner arches pay nothing. Raze it to end the grace.
 *
 * Engine note (0.28): there is no global EntityKilled message — Health.KilledBy
 * only notifies killer StatisticsTracker + Looter. The death signal used here
 * is OnGlobalOwnershipChanged(to=INVALID_PLAYER), the same broadcast vanilla's
 * EntityLimits uses to release population. Verified in-game (0.28.0): it fires
 * exactly once per destroyed entity, before OnDestroy, with Identity/Cost/
 * Health still queryable. A health==0 guard separates true deaths from the
 * other destruction paths that also broadcast to=-1 (promotion replacement,
 * delete/cheat removal, defeat cleanup) — those destroy entities at full HP.
 * Capture never destroys (ownership moves 1->2), so captured units pay nothing.
 * Deaths are processed at end-of-turn, so the arch's state is read at
 * processing time, not at damage time; each standing arch pays independently.
 * All guards fail closed (no refund) on missing interfaces.
 */
function LastShore() {}

LastShore.prototype.Schema =
	"<optional>" +
		"<element name='RefundPercent' a:help='Percent of each fallen unit cost refunded (default 15).'>" +
			"<data type='nonNegativeInteger'/>" +
		"</element>" +
	"</optional>";

LastShore.prototype.Init = function()
{
	this.refundPercent = this.template.RefundPercent ? +this.template.RefundPercent : 15;
};

/**
 * The grace flows only from a completed arch held by a living Lindon player.
 * Foundations (under construction), captured or gaia-held arches stay silent.
 */
LastShore.prototype.IsEmpowered = function()
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
	return !!cmpOwnerIdentity && cmpOwnerIdentity.GetCiv() == "lindon";
};

LastShore.prototype.GetOwner = function()
{
	const cmpOwnership = Engine.QueryInterface(this.entity, IID_Ownership);
	return cmpOwnership ? cmpOwnership.GetOwner() : INVALID_PLAYER;
};

/** Only Lindon units count: no structures, foundations, heroes, or wonders. */
LastShore.prototype.IsRefundable = function(ent)
{
	if (Engine.QueryInterface(ent, IID_Foundation))
		return false;
	const cmpIdentity = Engine.QueryInterface(ent, IID_Identity);
	if (!cmpIdentity)
		return false;
	if (!cmpIdentity.HasClass("Unit"))
		return false;
	if (cmpIdentity.HasClass("Hero") || cmpIdentity.HasClass("Wonder"))
		return false;
	return true;
};

LastShore.prototype.Refund = function(owner, ent)
{
	const cmpCost = Engine.QueryInterface(ent, IID_Cost);
	if (!cmpCost || !cmpCost.GetResourceCosts)
		return;
	const costs = cmpCost.GetResourceCosts();
	if (!costs)
		return;

	const cmpPlayerManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_PlayerManager);
	const cmpPlayer = Engine.QueryInterface(cmpPlayerManager.GetPlayerByID(owner), IID_Player);
	if (!cmpPlayer || !cmpPlayer.AddResource)
		return;

	for (const res in costs)
	{
		const amount = Math.floor(costs[res] * this.refundPercent / 100);
		if (amount > 0)
			cmpPlayer.AddResource(res, amount);
	}
};

/**
 * Death signal: every destroyed entity broadcasts ownership -> INVALID.
 * msg.from is the owner at the moment of death (the entity's own Ownership
 * already reads INVALID_PLAYER here). Only the arch's current owner's true
 * deaths refund: the health==0 guard drops promotion replacements and other
 * alive-destructions, and IsEmpowered drops foundations/captured/defeated.
 */
LastShore.prototype.OnGlobalOwnershipChanged = function(msg)
{
	if (msg.to !== INVALID_PLAYER || msg.from === INVALID_PLAYER)
		return;

	if (!this.IsEmpowered() || msg.from !== this.GetOwner())
		return;

	const cmpHealth = Engine.QueryInterface(msg.entity, IID_Health);
	if (!cmpHealth || cmpHealth.GetHitpoints() > 0)
		return;

	if (!this.IsRefundable(msg.entity))
		return;

	this.Refund(msg.from, msg.entity);
};

Engine.RegisterComponentType(IID_LastShore, "LastShore", LastShore);
