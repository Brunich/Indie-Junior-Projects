## WeatherSystem — Battle weather effects
extends RefCounted
class_name WeatherSystem

enum Weather { NONE, RAIN, SUN, SANDSTORM, HAIL, HARSH_SUN, HEAVY_RAIN }

static func get_move_modifier(move_type: String, weather: Weather) -> float:
	match weather:
		Weather.RAIN:
			if move_type == "Water":  return 1.5
			if move_type == "Fire":   return 0.5
		Weather.SUN:
			if move_type == "Fire":   return 1.5
			if move_type == "Water":  return 0.5
		Weather.HARSH_SUN:
			if move_type == "Fire":   return 1.5
			if move_type == "Water":  return 0.0  ## Water moves fail
		Weather.HEAVY_RAIN:
			if move_type == "Water":  return 1.5
			if move_type == "Fire":   return 0.0  ## Fire moves fail
	return 1.0

static func get_end_of_turn_damage(creature, weather: Weather) -> int:
	match weather:
		Weather.SANDSTORM:
			if creature.type1 not in ["Rock","Steel","Ground"] and creature.type2 not in ["Rock","Steel","Ground"]:
				if creature.ability not in ["Sand Veil","Sand Rush","Sand Force","Magic Guard","Overcoat"]:
					return max(1, creature.max_hp / 16)
		Weather.HAIL:
			if creature.type1 != "Ice" and creature.type2 != "Ice":
				if creature.ability not in ["Snow Cloak","Slush Rush","Ice Body","Magic Guard","Overcoat"]:
					return max(1, creature.max_hp / 16)
	return 0

static func get_accuracy_modifier(move_name: String, weather: Weather) -> float:
	if move_name == "Thunder" and weather == Weather.RAIN:   return 999.0 ## Always hits
	if move_name == "Blizzard" and weather == Weather.HAIL:  return 999.0
	if move_name == "Hurricane" and weather == Weather.RAIN: return 999.0
	if move_name == "Thunder" and weather == Weather.SUN:    return 0.5
	if move_name == "Hurricane" and weather == Weather.SUN:  return 0.5
	return 1.0

static func get_description(weather: Weather) -> String:
	match weather:
		Weather.RAIN:       return "Rain is falling."
		Weather.SUN:        return "The sunlight is harsh."
		Weather.SANDSTORM:  return "A sandstorm is raging."
		Weather.HAIL:       return "Hail is falling."
		Weather.HARSH_SUN:  return "The sunlight is extremely harsh!"
		Weather.HEAVY_RAIN: return "Heavy rain is pouring!"
	return ""
