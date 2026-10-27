function RangerAmbush() {}

RangerAmbush.prototype.Schema =
	"<optional>" +
		"<element name='BonusPercent' a:help='Percent bonus to the first ranged attack launched from concealment against an unaware target (default 50).'>" +
			"<data type='positiveInteger'/>" +
		"</element>" +
	"</optional>";

RangerAmbush.prototype.Init = function()
{
	this.bonusPercent = this.template.BonusPercent ? +this.template.BonusPercent : 50;
	this.armed = false;
};

RangerAmbush.prototype.Arm = function()
{
	this.armed = true;
};

RangerAmbush.prototype.Clear = function()
{
	this.armed = false;
};

RangerAmbush.prototype.IsArmed = function()
{
	return this.armed;
};

RangerAmbush.prototype.Consume = function()
{
	this.armed = false;
	return DeriveModificationsFromTech({
		"modifications": [
			{ "value": "Attack/Ranged/Damage/Hack", "multiply": 1 + this.bonusPercent / 100 },
			{ "value": "Attack/Ranged/Damage/Pierce", "multiply": 1 + this.bonusPercent / 100 },
			{ "value": "Attack/Ranged/Damage/Crush", "multiply": 1 + this.bonusPercent / 100 }
		]
	});
};

RangerAmbush.prototype.OnDestroy = function()
{
	this.Clear();
	const cmpModifiersManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_ModifiersManager);
	if (cmpModifiersManager)
		cmpModifiersManager.RemoveAllModifiers("doriath-ranger-ambush", this.entity);
};

Engine.RegisterComponentType(IID_RangerAmbush, "RangerAmbush", RangerAmbush);

// Attack has no per-strike message; wrap its launch method so the modifier
// exists only while this Ranger's first concealed shot is being calculated.
const g_RangerAmbushOriginalPerformAttack = Attack.prototype.PerformAttack;

Attack.prototype.PerformAttack = function(type, target)
{
	const cmpAmbush = Engine.QueryInterface(this.entity, IID_RangerAmbush);
	if (type != "Ranged" || !cmpAmbush || !cmpAmbush.IsArmed())
		return g_RangerAmbushOriginalPerformAttack.call(this, type, target);

	const cmpPosition = Engine.QueryInterface(this.entity, IID_Position);
	const cmpTargetPosition = Engine.QueryInterface(target, IID_Position);
	const cmpOwnership = Engine.QueryInterface(this.entity, IID_Ownership);
	if (!cmpPosition || !cmpPosition.IsInWorld() ||
	    !cmpTargetPosition || !cmpTargetPosition.IsInWorld() ||
	    !cmpOwnership)
		return g_RangerAmbushOriginalPerformAttack.call(this, type, target);

	const cmpModifiersManager = Engine.QueryInterface(SYSTEM_ENTITY, IID_ModifiersManager);
	const modifiers = cmpAmbush.Consume();
	cmpModifiersManager.AddModifiers("doriath-ranger-ambush", modifiers, this.entity);

	try
	{
		return g_RangerAmbushOriginalPerformAttack.call(this, type, target);
	}
	finally
	{
		cmpModifiersManager.RemoveAllModifiers("doriath-ranger-ambush", this.entity);
	}
};
