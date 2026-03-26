extends Node

## SaveSystem - Static save/load handler using JSON
## Saves to user://emberveil_save.json

const SAVE_PATH = "user://emberveil_save.json"

## Check if a save file exists
static func save_exists() -> bool:
	return FileAccess.file_exists(SAVE_PATH)

## Save the game state from GameManager
static func save_game(game_manager: Node) -> bool:
	var save_dict = {
		"version": "1.2",
		"player_name": game_manager.player_name,
		"region_name": game_manager.current_region,
		"playtime_seconds": game_manager.playtime_seconds,
		"save_scene": game_manager.save_scene,
		"save_position": {
			"x": game_manager.save_position.x,
			"y": game_manager.save_position.y,
		},
		"pending_spawn_id": game_manager.pending_spawn_id,
		"checkpoint_scene": game_manager.checkpoint_scene,
		"checkpoint_spawn_id": game_manager.checkpoint_spawn_id,
		"checkpoint_position": {
			"x": game_manager.checkpoint_position.x,
			"y": game_manager.checkpoint_position.y,
		},
		"party": _serialize_party(game_manager.party),
		"storage_box": _serialize_party(game_manager.storage_box),
		"badges": game_manager.badges,
		"money": game_manager.money,
		"inventory": InventorySystem.get_snapshot(),
		"flags": game_manager.flags,
		"caught_ids": game_manager.caught_ids,
		"seen_ids": game_manager.seen_ids
	}

	var json_string = JSON.stringify(save_dict)
	var file = FileAccess.open(SAVE_PATH, FileAccess.WRITE)

	if file == null:
		print("SaveSystem: Error opening file for writing at ", SAVE_PATH)
		return false

	file.store_string(json_string)
	print("SaveSystem: Game saved successfully to ", SAVE_PATH)
	return true

## Load the game state and return as Dictionary
static func load_game() -> Dictionary:
	if not save_exists():
		print("SaveSystem: No save file found at ", SAVE_PATH)
		return {}

	var file = FileAccess.open(SAVE_PATH, FileAccess.READ)

	if file == null:
		print("SaveSystem: Error opening file for reading at ", SAVE_PATH)
		return {}

	var json_string = file.get_as_text()
	var json = JSON.new()
	var error = json.parse(json_string)

	if error != OK:
		print("SaveSystem: JSON parse error: ", json.get_error_message())
		return {}

	var save_dict = json.data
	print("SaveSystem: Game loaded successfully from ", SAVE_PATH)
	return save_dict

## Delete the save file
static func delete_save() -> bool:
	if not save_exists():
		print("SaveSystem: No save file to delete")
		return false

	var error = DirAccess.remove_absolute(SAVE_PATH)

	if error != OK:
		print("SaveSystem: Error deleting save file: ", error)
		return false

	print("SaveSystem: Save file deleted")
	return true

## Serialize party array of CreatureInstance objects to dictionaries
static func _serialize_party(party: Array) -> Array:
	var serialized = []

	for creature in party:
		var creature_dict = {
			"id":       creature.creature_id,
			"nickname": creature.nickname,
			"skin":     creature.active_skin,
			"nature":   creature.nature,
			"ability":  creature.ability,
			"held_item": creature.held_item,
			"catch_rate": creature.catch_rate,
			"iv_hp":    creature.iv_hp,
			"iv_atk":   creature.iv_atk,
			"iv_def":   creature.iv_def,
			"iv_sp_atk": creature.iv_sp_atk,
			"iv_sp_def": creature.iv_sp_def,
			"iv_speed": creature.iv_speed,
			"level":    creature.level,
			"bond":     creature.bond,
			"hp_cur":   creature.hp_cur,
			"hp_max":   creature.hp_max,
			"exp":      creature.experience,
			"status":   creature.status,
			"type1":    creature.type1,
			"type2":    creature.type2,
			"moves":    _serialize_moves(creature.moves, creature.moves_pp)
		}
		serialized.append(creature_dict)

	return serialized

## Serialize moves con su PP actual (moves_pp es array paralelo)
static func _serialize_moves(moves: Array, moves_pp: Array) -> Array:
	var serialized = []
	for i in moves.size():
		var move : MoveData = moves[i]
		var move_dict = {
			"name":   move.move_name,
			"pp":     moves_pp[i] if i < moves_pp.size() else move.pp_max,
			"pp_max": move.pp_max
		}
		serialized.append(move_dict)
	return serialized
