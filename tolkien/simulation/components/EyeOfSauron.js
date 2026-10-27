/**
 * EyeOfSauron — Barad-dûr's search-only gaze (Mordor).
 *
 * Search-only by design: no global map reveal (Sauron's attention is finite
 * per lore; the engine also exposes no shroud-reveal script API, and
 * map-covering vision ranges risk perf costs). Instead, a single short-lived
 * "seer" entity hops between enemy strongholds on a fixed schedule:
 * deterministic (fixed priority sort + fixed timings, no RNG), unpathable
 * terrain and water are irrelevant (Position.JumpTo), and slaying the seer
 * ends that gaze early (emergent counterplay).
 *
 * Cycle: cooldown (~8 min) -> auto-cast with a global warning -> waypoint
 * search (~40s) -> cooldown. The ability lives and dies with Barad-dûr:
 * capture or destruction ends it. Requires a completed wonder (gated on
 * the Foundation component) owned by a Mordor-civ player.
 *
 * Verified engine APIs used: Timer.SetInterval/GetTime (cf. Visibility.js),
 * RangeManager.ExecuteQuery(entity, min, max, players, iid, onlyVisible)
 * with onlyVisible=false for fogged targets (cf. UnitAI dropsite search),
 * Position.JumpTo (cf. Health.js), Ownership.SetOwner, Engine.AddEntity /
 * Engine.DestroyEntity (cf. Health.js), GuiInterface.AddTimeNotification
 * (cf. CeasefireManager.js).
 */
function EyeOfSauron() {}

EyeOfSauron.prototype.Schema =
	"<optional>" +
		"<element name='Cooldown' a:help='Ms between searches (default 480000 = ~8 min).'>" +
			"<data type='nonNegativeInteger'/>" +
		"</element>" +
	"</optional>" +
	"<optional>" +
		"<element name='WaypointLinger' a:help='Ms the seer spends at each waypoint (default 4000).'>" +
			"<data type='nonNegativeInteger'/>" +
		"</element>" +
	"</optional>" +
	"<optional>" +
		"<element name='MaxWaypoints' a:help='Max strongholds visited per search (default 10).'>" +
			"<data type='nonNegativeInteger'/>" +
		"</element>" +
	"</optional>" +
	"<optional>" +
		"<element name='QueryRadius' a:help='Asset-hunt radius around Barad-dûr (default 1500).'>" +
			"<data type='nonNegativeInteger'/>" +
		"</element>" +
	"</optional>" +
	"<optional>" +
		"<element name='SeerTemplate' a:help='Seer entity template (default units/mordor/eye_seer).'>" +
			"<text/>" +
		"</element>" +
	"</optional>";

EyeOfSauron.prototype.Init = function()
{
	this.cooldown = this.template.Cooldown ? +this.template.Cooldown : 480000;
	this.linger = this.template.WaypointLinger ? +this.template.WaypointLinger : 4000;
	this.maxWaypoints = this.template.MaxWaypoints ? +this.template.MaxWaypoints : 10;
	this.queryRadius = this.template.QueryRadius ? +this.template.QueryRadius : 1500;
	this.seerTemplate = "units/mordor/eye_seer";
	if (this.template.SeerTemplate)
		this.seerTemplate = typeof this.template.SeerTemplate == "string" ?
			this.template.SeerTemplate :
			this.template.SeerTemplate._string || this.seerTemplate;

	this.phase = "cooldown";
	this.nextCastTime = 0;
	this.waypoints = [];
	this.waypointIndex = 0;
	this.nextHopTime = 0;
	this.seer = INVALID_ENTITY;
	this.firstTickDone = false;

	const cmpTimer = Engine.QueryInterface(SYSTEM_ENTITY, IID_Timer);
	cmpTimer.SetInterval(this.entity, IID_EyeOfSauron, "EyeTick", 1000, 1000);
};

/**
 * The Eye only serves its builder: a completed wonder held by Mordor.
 * Foundations (under construction), captured or gaia-held towers stay dark.
 */
EyeOfSauron.prototype.IsEmpowered = function()
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
	if (!cmpPlayer)
		return false;
	// Player entities carry their civ on Identity (cf. Player.js template
	// expansion); there is no Player.GetCiv.
	const cmpOwnerIdentity = Engine.QueryInterface(cmpPlayerManager.GetPlayerByID(owner), IID_Identity);
	if (!cmpOwnerIdentity || cmpOwnerIdentity.GetCiv() != "mordor")
		return false;
	if (cmpPlayer.IsDefeated && cmpPlayer.IsDefeated())
		return false;

	return true;
};

EyeOfSauron.prototype.GetOwner = function()
{
	return Engine.QueryInterface(this.entity, IID_Ownership).GetOwner();
};

EyeOfSauron.prototype.DestroySeer = function()
{
	if (this.seer == INVALID_ENTITY)
		return;
	// The seer may already be gone (slain as counterplay, or cleaned up).
	if (Engine.QueryInterface(this.seer, IID_Position))
		Engine.DestroyEntity(this.seer);
	this.seer = INVALID_ENTITY;
};

EyeOfSauron.prototype.WarnAll = function(message, duration)
{
	const cmpGuiInterface = Engine.QueryInterface(SYSTEM_ENTITY, IID_GuiInterface);
	if (!cmpGuiInterface)
		return;
	cmpGuiInterface.AddTimeNotification({
		"message": message,
		"translateMessage": true
	}, duration || 8000);
};

/**
 * Enemy strongholds, highest value first: heroes, wonders, fortresses,
 * civic centres, then anything else. Fixed priority + entity-id tiebreak
 * keeps lockstep simulations identical. Fogged/shrouded assets are
 * included on purpose — the Eye is drawn to strength it cannot see.
 */
EyeOfSauron.prototype.FindWaypoints = function(owner)
{
	const cmpPlayerManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_PlayerManager);
	const cmpOwnerDiplomacy = Engine.QueryInterface(cmpPlayerManager.GetPlayerByID(owner), IID_Diplomacy);
	if (!cmpOwnerDiplomacy)
		return [];

	const enemies = [];
	for (const p of cmpPlayerManager.GetNonGaiaPlayers())
		if (p != owner && cmpOwnerDiplomacy.IsEnemy(p))
			enemies.push(p);
	if (!enemies.length)
		return [];

	const cmpRangeManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_RangeManager);
	// onlyVisible=false: fogged targets included (cf. UnitAI dropsite search).
	const buildings = cmpRangeManager.ExecuteQuery(this.entity, 0, this.queryRadius, enemies, IID_BuildingAI, false);
	const soldiers = cmpRangeManager.ExecuteQuery(this.entity, 0, this.queryRadius, enemies, IID_UnitAI, false);

	const found = [];
	for (const ent of buildings.concat(soldiers))
	{
		const cmpIdentity = Engine.QueryInterface(ent, IID_Identity);
		if (!cmpIdentity)
			continue;
		let priority = 4;
		if (cmpIdentity.HasClass("Hero"))
			priority = 0;
		else if (cmpIdentity.HasClass("Wonder"))
			priority = 1;
		else if (cmpIdentity.HasClass("Fortress"))
			priority = 2;
		else if (cmpIdentity.HasClass("CivCentre"))
			priority = 3;
		else if (!cmpIdentity.HasClass("Human") && !cmpIdentity.HasClass("Unit"))
			priority = 5;

		const cmpPosition = Engine.QueryInterface(ent, IID_Position);
		if (!cmpPosition || !cmpPosition.IsInWorld())
			continue;
		const pos = cmpPosition.GetPosition2D();
		found.push({ "priority": priority, "ent": ent, "x": pos.x, "z": pos.y });
	}

	found.sort((a, b) => (a.priority - b.priority) || (a.ent - b.ent));
	return found.slice(0, this.maxWaypoints);
};

EyeOfSauron.prototype.TryCast = function(owner, now)
{
	const waypoints = this.FindWaypoints(owner);
	// Stand-off: watch each stronghold from nearby instead of landing in its
	// courtyard (a 30-HP crow dropped on an enemy CC dies in under a second).
	// Pull every waypoint a quarter of the way toward Barad-dûr: deterministic,
	// always in-bounds on rectangular maps, keeps counterplay (focused bows
	// still banish the gaze) while letting each linger contribute.
	const cmpOwnPosition = Engine.QueryInterface(this.entity, IID_Position);
	if (cmpOwnPosition && cmpOwnPosition.IsInWorld())
	{
		const home = cmpOwnPosition.GetPosition2D();
		for (const wp of waypoints)
		{
			wp.x += (home.x - wp.x) * 0.25;
			wp.z += (home.y - wp.z) * 0.25;
		}
	}
	if (!waypoints.length)
	{
		// Nothing worth gazing at (or nothing left): stay dark, retry soon
		// without burning the long cooldown.
		this.nextCastTime = now + 30000;
		return;
	}

	this.seer = Engine.AddEntity(this.seerTemplate);
	if (this.seer == INVALID_ENTITY)
	{
		this.nextCastTime = now + 30000;
		return;
	}
	const cmpSeerOwnership = Engine.QueryInterface(this.seer, IID_Ownership);
	if (cmpSeerOwnership)
		cmpSeerOwnership.SetOwner(owner);
	const cmpSeerPosition = Engine.QueryInterface(this.seer, IID_Position);
	if (!cmpSeerPosition)
	{
		this.DestroySeer();
		this.nextCastTime = now + 30000;
		return;
	}
	cmpSeerPosition.JumpTo(waypoints[0].x, waypoints[0].z);

	this.waypoints = waypoints;
	this.waypointIndex = 1;
	this.nextHopTime = now + this.linger;
	this.phase = "search";

	this.WarnAll("The Eye of Sauron Opens — no shadow escapes the Gaze.", 8000);
};

EyeOfSauron.prototype.HopSeer = function(now)
{
	if (this.waypointIndex >= this.waypoints.length)
	{
		this.EndSearch("The Eye Turns Elsewhere.");
		return;
	}
	const cmpSeerPosition = Engine.QueryInterface(this.seer, IID_Position);
	if (!cmpSeerPosition || !cmpSeerPosition.IsInWorld())
	{
		// The gaze was banished (seer slain or lost): counterplay works.
		this.EndSearch("");
		return;
	}
	const wp = this.waypoints[this.waypointIndex++];
	cmpSeerPosition.JumpTo(wp.x, wp.z);
	this.nextHopTime = now + this.linger;
};

EyeOfSauron.prototype.EndSearch = function(message)
{
	this.DestroySeer();
	this.waypoints = [];
	this.waypointIndex = 0;
	this.phase = "cooldown";
	this.nextCastTime = Engine.QueryInterface(SYSTEM_ENTITY, IID_Timer).GetTime() + this.cooldown;
	if (message)
		this.WarnAll(message, 6000);
};

EyeOfSauron.prototype.EyeTick = function()
{
	if (!this.IsEmpowered())
	{
		// Captured, unfinished, or ownerless: no gaze, and no lingering seer.
		if (this.phase == "search")
			this.EndSearch("");
		else
			this.DestroySeer();
		return;
	}

	const now = Engine.QueryInterface(SYSTEM_ENTITY, IID_Timer).GetTime();

	if (!this.firstTickDone)
	{
		// Grace period after completion before the first gaze.
		this.firstTickDone = true;
		this.nextCastTime = now + 30000;
	}

	if (this.phase == "cooldown")
	{
		if (now >= this.nextCastTime)
			this.TryCast(this.GetOwner(), now);
		return;
	}

	// Search phase: the seer may have been slain — check before hopping.
	if (this.seer == INVALID_ENTITY || !Engine.QueryInterface(this.seer, IID_Position))
	{
		this.EndSearch("");
		return;
	}
	if (now >= this.nextHopTime)
		this.HopSeer(now);
};

EyeOfSauron.prototype.OnDestroy = function()
{
	this.DestroySeer();
};

Engine.RegisterComponentType(IID_EyeOfSauron, "EyeOfSauron", EyeOfSauron);
