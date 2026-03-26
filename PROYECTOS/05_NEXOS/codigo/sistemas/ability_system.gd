## AbilitySystem — Handles ability triggers in battle
## Called by BattleManager at appropriate moments
extends RefCounted
class_name AbilitySystem

## ── Passive triggers ──────────────────────────────────────────────────────────
## Called when a creature enters battle
static func on_enter(creature, battle_state: Dictionary) -> Array:
	var effects := []
	match creature.ability:
		"Intimidate":
			effects.append({"type":"stat_change","target":"enemy","stat":"atk","stages":-1,"msg":"%s's Intimidate cut %s's Attack!" % [creature.nickname, battle_state.enemy.nickname]})
		"Drizzle":
			effects.append({"type":"weather","value":"rain","msg":"%s's Drizzle summoned rain!" % creature.nickname})
		"Drought":
			effects.append({"type":"weather","value":"sun","msg":"%s's Drought intensified the sun!" % creature.nickname})
		"Sand Stream":
			effects.append({"type":"weather","value":"sandstorm","msg":"%s's Sand Stream whipped up a sandstorm!" % creature.nickname})
		"Snow Warning":
			effects.append({"type":"weather","value":"hail","msg":"%s's Snow Warning summoned hail!" % creature.nickname})
		"Pressure":
			effects.append({"type":"message","msg":"%s is exerting its Pressure!" % creature.nickname})
		"Shadow Shield":
			effects.append({"type":"message","msg":"%s's Shadow Shield is active!" % creature.nickname})
		"Multiscale":
			effects.append({"type":"message","msg":"%s's Multiscale protects it!" % creature.nickname})
	return effects

## Called when a move is used — modifies power/type/accuracy
static func on_move_use(attacker, move: Dictionary, target) -> Dictionary:
	var modified := move.duplicate()
	match attacker.ability:
		"Technician":
			if modified.get("power", 99) <= 60:
				modified["power"] = int(modified["power"] * 1.5)
		"Iron Fist":
			if "punch" in modified.get("flags", []):
				modified["power"] = int(modified["power"] * 1.2)
		"Adaptability":
			modified["stab_bonus"] = 2.0  ## STAB is 2× instead of 1.5×
		"Mold Breaker":
			modified["ignore_ability"] = true
		"Refrigerate":
			if modified.get("type") == "Normal":
				modified["type"] = "Ice"
				modified["power"] = int(modified["power"] * 1.2)
		"Solar Power":
			if modified.get("category") == "Special":
				modified["power"] = int(modified["power"] * 1.5) ## In sun
		"Chlorophyll":
			pass  ## Handled in speed calculation
		"Swift Swim":
			pass  ## Handled in speed calculation
	return modified

## Called when creature takes damage
static func on_take_hit(creature, damage: int, move: Dictionary) -> Dictionary:
	var result := {"damage": damage, "effects": []}
	match creature.ability:
		"Shadow Shield", "Multiscale":
			if creature.current_hp == creature.max_hp:
				result["damage"] = damage / 2
				result["effects"].append({"type":"message","msg":"%s's %s halved the damage!" % [creature.nickname, creature.ability]})
		"Sturdy":
			if creature.current_hp == creature.max_hp and damage >= creature.current_hp:
				result["damage"] = creature.current_hp - 1
				result["effects"].append({"type":"message","msg":"%s hung on thanks to Sturdy!" % creature.nickname})
		"Filter", "Solid Rock":
			var mult = move.get("effectiveness_mult", 1.0)
			if mult > 1.0:
				result["damage"] = int(damage * 0.75)
		"Rough Skin", "Iron Barbs":
			if move.get("contact", false):
				result["effects"].append({"type":"damage_attacker","amount":int(move.get("attacker_max_hp", 100) / 8.0)})
		"Cursed Body":
			if randf() < 0.3:
				result["effects"].append({"type":"disable_move","msg":"%s's Cursed Body disabled %s!" % [creature.nickname, move.get("name","move")]})
	return result

## Speed modifier from ability
static func get_speed_modifier(creature, weather: String) -> float:
	match creature.ability:
		"Swift Swim":    return 2.0 if weather == "rain" else 1.0
		"Chlorophyll":   return 2.0 if weather == "sun"  else 1.0
		"Sand Rush":     return 2.0 if weather == "sandstorm" else 1.0
		"Slush Rush":    return 2.0 if weather == "hail" else 1.0
		"Quick Feet":    return 1.5 if creature.status != "" else 1.0
		"Unburden":      return 2.0 if creature.get("lost_item", false) else 1.0
	return 1.0
