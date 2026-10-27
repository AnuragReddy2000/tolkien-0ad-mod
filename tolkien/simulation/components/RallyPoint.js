function RallyPoint() {}

RallyPoint.prototype.Schema =
	"<a:component/>" +
	"<optional>" +
		"<element name='TunnelLink' a:help='Moria tunnel network (opt-in). When present, this building is a tunnel mouth: setting its rally point onto another friendly tunnel mouth links them, and garrisoned owner units are transferred after TransferDelay.'>" +
			"<element name='TransferDelay' a:help='Milliseconds units spend travelling the deep ways before emerging at the linked mouth.'>" +
				"<data type='positiveInteger'/>" +
			"</element>" +
		"</element>" +
	"</optional>";

RallyPoint.prototype.Init = function()
{
	this.pos = [];
	this.data = [];

	// === Tolkien mod: tunnel network (Moria) ===
	// Gated entirely by the presence of a <TunnelLink> block in this
	// component's template. Entities without it are completely unaffected:
	// vanilla rally behaviour only, no timers, no transfers.
	this.tunnel = null;
	this.transferTimer = 0;
	this.lastTransfer = {};
	// NB: marker entities carry no <RallyPoint> template element, so
	// this.template is undefined for them — guard before reading it.
	if (this.template && this.template.TunnelLink)
		this.tunnel = {
			"transferDelay": +this.template.TunnelLink.TransferDelay
		};
};

RallyPoint.prototype.AddPosition = function(x, z)
{
	this.pos.push({
		"x": x,
		"z": z
	});
};

RallyPoint.prototype.HasPositions = function()
{
	return this.pos.length > 0;
};

RallyPoint.prototype.GetFirstPosition = function()
{
	return this.pos.length ? Vector2D.from3D(this.pos[0]) : new Vector2D(-1, -1);
};

RallyPoint.prototype.GetPositions = function()
{
	// Update positions for moving target entities

	var cmpRangeManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_RangeManager);
	var cmpOwnership = Engine.QueryInterface(this.entity, IID_Ownership);

	// We must not affect the simulation state here (modifications of the
	// RallyPointRenderer are allowed though), so copy the state
	var ret = [];
	for (var i = 0; i < this.pos.length; i++)
	{
		ret.push(this.pos[i]);

		// Update the rallypoint coordinates if the target is alive
		if (!this.data[i] || !this.data[i].target || !this.TargetIsAlive(this.data[i].target))
			continue;

		// and visible
		if (cmpRangeManager && cmpOwnership &&
				cmpRangeManager.GetLosVisibility(this.data[i].target, cmpOwnership.GetOwner()) != "visible")
			continue;

		// Get the actual position of the target entity
		var cmpPosition = Engine.QueryInterface(this.data[i].target, IID_Position);
		if (!cmpPosition || !cmpPosition.IsInWorld())
			continue;

		var targetPosition = cmpPosition.GetPosition2D();
		if (!targetPosition)
			continue;

		if (this.pos[i].x == targetPosition.x && this.pos[i].z == targetPosition.y)
			continue;

		ret[i] = { "x": targetPosition.x, "z": targetPosition.y };
		var cmpRallyPointRenderer = Engine.QueryInterface(this.entity, IID_RallyPointRenderer);
		if (cmpRallyPointRenderer)
			cmpRallyPointRenderer.UpdatePosition(i, targetPosition);
	}

	return ret;
};

// Extra data for the rally point, should have a command property and then helpful data for that command
// See getActionInfo in gui/input.js
RallyPoint.prototype.AddData = function(data)
{
	this.data.push(data);
};

// Returns an array with the data associated with this rally point.  Each element has the structure:
// {"type": "walk/gather/garrison/...", "target": targetEntityId, "resourceType": "tree/fruit/ore/..."} where target
// and resourceType (specific resource type) are optional, also target may be an invalid entity, check for existence.
RallyPoint.prototype.GetData = function()
{
	return this.data;
};

RallyPoint.prototype.Unset = function()
{
	this.pos = [];
	this.data = [];
};

RallyPoint.prototype.Reset = function()
{
	this.Unset();
	var cmpRallyPointRenderer = Engine.QueryInterface(this.entity, IID_RallyPointRenderer);
	if (cmpRallyPointRenderer)
		cmpRallyPointRenderer.Reset();
};

/**
 * @param {number} entity - The entity ID of the entity to order to the rally point.
 * @param {string[]} ignore - The commands to ignore when performed on this.entity.
 *				E.g. "garrison" when unloading.
 */
RallyPoint.prototype.OrderToRallyPoint = function(entity, ignore = [])
{
	let cmpOwnership = Engine.QueryInterface(this.entity, IID_Ownership);
	if (!cmpOwnership)
		return;
	let owner = cmpOwnership.GetOwner();

	let cmpEntOwnership = Engine.QueryInterface(entity, IID_Ownership);
	if (!cmpEntOwnership || cmpEntOwnership.GetOwner() != owner)
		return;

	let commands = GetRallyPointCommands(this, [entity]);
	if (!commands.length ||
		commands[0].target == this.entity && ignore.includes(commands[0].type))
		return;

	for (let command of commands)
		ProcessCommand(owner, command);
};

RallyPoint.prototype.OnGlobalEntityRenamed = function(msg)
{
	for (let data of this.data)
	{
		if (!data)
			continue;
		if (data.target && data.target == msg.entity)
			data.target = msg.newentity;
		if (data.source && data.source == msg.entity)
			data.source = msg.newentity;
	}

	if (msg.entity != this.entity)
		return;

	let cmpRallyPointNew = Engine.QueryInterface(msg.newentity, IID_RallyPoint);
	if (cmpRallyPointNew)
	{
		let rallyCoords = this.GetPositions();
		let rallyData = this.GetData();
		for (let i = 0; i < rallyCoords.length; ++i)
		{
			cmpRallyPointNew.AddPosition(rallyCoords[i].x, rallyCoords[i].z);
			cmpRallyPointNew.AddData(rallyData[i]);
		}
	}
};

RallyPoint.prototype.OnOwnershipChanged = function(msg)
{
	// No need to reset when constructing or destructing the entity
	if (msg.from == INVALID_PLAYER || msg.to == INVALID_PLAYER)
		return;

	this.Reset();
	// Tunnel links do not survive capture: the new owner must re-link.
	this.CancelTransfer();
	this.lastTransfer = {};
};

/**
 * Returns true if the target exists and has non-zero hitpoints.
 */
RallyPoint.prototype.TargetIsAlive = function(ent)
{
	var cmpFormation = Engine.QueryInterface(ent, IID_Formation);
	if (cmpFormation)
		return true;

	var cmpHealth = QueryMiragedInterface(ent, IID_Health);
	return cmpHealth && cmpHealth.GetHitpoints() != 0;
};

// === Tolkien mod: tunnel network (Moria) ===
//
// Market-like linking: the mouth's rally point, when set onto another living
// tunnel mouth of the same owner, is the link. Garrisoned owner units are
// unloaded at this mouth, then moved to the linked mouth, where they emerge
// OUTSIDE and idle: arrivals never re-garrison on their own, so there is no
// ping-pong loop by construction. A per-unit timestamp guard covers manual
// re-garrison edge cases. No randomness is used anywhere: fully deterministic.

RallyPoint.prototype.GetOwner = function()
{
	let cmpOwnership = Engine.QueryInterface(this.entity, IID_Ownership);
	return cmpOwnership ? cmpOwnership.GetOwner() : INVALID_PLAYER;
};

/**
 * @return {number} - The linked tunnel mouth, or INVALID_ENTITY when this
 * mouth is unlinked, the target is dead, foreign-owned, or not a mouth.
 */
RallyPoint.prototype.GetLinkedMouth = function()
{
	if (!this.tunnel)
		return INVALID_ENTITY;

	let owner = this.GetOwner();
	if (owner == INVALID_PLAYER)
		return INVALID_ENTITY;

	for (let datum of this.data)
	{
		if (!datum || datum.target === undefined)
			continue;
		let target = datum.target;
		if (target == this.entity)
			continue;
		let cmpPosition = Engine.QueryInterface(target, IID_Position);
		if (!cmpPosition || !cmpPosition.IsInWorld())
			continue;
		if (!this.TargetIsAlive(target))
			continue;
		let cmpTargetOwnership = Engine.QueryInterface(target, IID_Ownership);
		if (!cmpTargetOwnership || cmpTargetOwnership.GetOwner() != owner)
			continue;
		let cmpTargetRally = Engine.QueryInterface(target, IID_RallyPoint);
		if (!cmpTargetRally || !cmpTargetRally.tunnel)
			continue;
		return target;
	}
	return INVALID_ENTITY;
};

RallyPoint.prototype.OnGarrisonedUnitsChanged = function(msg)
{
	if (!this.tunnel || !msg.added || !msg.added.length)
		return;
	if (!this.HasTransferCandidate(msg.added))
		return;
	this.ScheduleTransfer();
};

RallyPoint.prototype.HasTransferCandidate = function(entities)
{
	let owner = this.GetOwner();
	let now = this.TunnelNow();
	for (let ent of entities || [])
	{
		if (!this.IsOwnedBy(ent, owner))
			continue;
		if (!this.TransferCooldownElapsed(ent, now))
			continue;
		return true;
	}
	return false;
};

RallyPoint.prototype.IsOwnedBy = function(ent, owner)
{
	let cmpOwnership = Engine.QueryInterface(ent, IID_Ownership);
	return !!cmpOwnership && cmpOwnership.GetOwner() == owner;
};

RallyPoint.prototype.TunnelNow = function()
{
	let cmpTimer = Engine.QueryInterface(SYSTEM_ENTITY, IID_Timer);
	return cmpTimer ? cmpTimer.GetTime() : 0;
};

RallyPoint.prototype.TransferCooldownElapsed = function(ent, now)
{
	// A unit that just travelled may not travel again until twice the delay
	// has passed. Belt and suspenders alongside outside-arrival: manual
	// re-garrison can never set up a bounce loop.
	return now - (this.lastTransfer[ent] || -1e12) >= 2 * this.tunnel.transferDelay;
};

RallyPoint.prototype.ScheduleTransfer = function()
{
	if (this.transferTimer || !this.tunnel)
		return;
	let cmpTimer = Engine.QueryInterface(SYSTEM_ENTITY, IID_Timer);
	if (!cmpTimer)
		return;
	this.transferTimer = cmpTimer.SetTimeout(this.entity, IID_RallyPoint, "TunnelTransfer", this.tunnel.transferDelay, null);
};

RallyPoint.prototype.CancelTransfer = function()
{
	if (!this.transferTimer)
		return;
	let cmpTimer = Engine.QueryInterface(SYSTEM_ENTITY, IID_Timer);
	if (cmpTimer)
		cmpTimer.CancelTimer(this.transferTimer);
	this.transferTimer = 0;
};

RallyPoint.prototype.TunnelTransfer = function(data, lateness)
{
	this.transferTimer = 0;
	if (!this.tunnel)
		return;

	let target = this.GetLinkedMouth();
	if (target == INVALID_ENTITY)
		return;

	let cmpHolder = Engine.QueryInterface(this.entity, IID_GarrisonHolder);
	if (!cmpHolder)
		return;

	let cmpTargetPosition = Engine.QueryInterface(target, IID_Position);
	if (!cmpTargetPosition || !cmpTargetPosition.IsInWorld())
		return;
	let dest = cmpTargetPosition.GetPosition2D();
	if (!dest)
		return;

	let owner = this.GetOwner();
	let now = this.TunnelNow();
	let moved = 0;

	// Suppress this mouth's rally orders for the duration of the exit burst:
	// arrivals must emerge idle at the far mouth, never carrying a
	// re-garrison order back into the network. Save and restore verbatim.
	let savedPos = this.GetPositions();
	let savedData = this.GetData().slice();
	this.Reset();

	for (let ent of cmpHolder.GetEntities().slice())
	{
		if (!this.IsOwnedBy(ent, owner) || !this.TransferCooldownElapsed(ent, now))
			continue;
		if (!cmpHolder.Unload(ent))
			continue;
		let cmpPosition = Engine.QueryInterface(ent, IID_Position);
		if (!cmpPosition)
			continue;
		// Deterministic fan-out around the far mouth (golden angle, no RNG).
		let angle = moved * 2.399963;
		let radius = 4 + Math.floor(moved / 8) * 2;
		cmpPosition.JumpTo(dest.x + radius * Math.cos(angle), dest.y + radius * Math.sin(angle));
		cmpPosition.SetHeightOffset(0);
		this.lastTransfer[ent] = now;
		++moved;
	}

	for (let i = 0; i < savedPos.length; ++i)
	{
		this.AddPosition(savedPos[i].x, savedPos[i].z);
		this.AddData(savedData[i]);
	}

	// Prune travel stamps of entities that no longer exist.
	for (let ent in this.lastTransfer)
		if (!Engine.QueryInterface(+ent, IID_Health))
			delete this.lastTransfer[ent];

	// Keep the shuttle running while owner units remain inside.
	if (moved && this.HasTransferCandidate(cmpHolder.GetEntities()))
		this.ScheduleTransfer();
	else if (!moved)
	{
		// Nothing was eligible (cooldown-held or foreign shelterers):
		// retry once the cooldown could have elapsed.
		let cmpTimer = Engine.QueryInterface(SYSTEM_ENTITY, IID_Timer);
		if (cmpTimer && cmpHolder.GetEntities().length)
			this.transferTimer = cmpTimer.SetTimeout(this.entity, IID_RallyPoint, "TunnelTransfer", this.tunnel.transferDelay, null);
	}
};

RallyPoint.prototype.OnDestroy = function()
{
	this.CancelTransfer();
};

Engine.RegisterComponentType(IID_RallyPoint, "RallyPoint", RallyPoint);
