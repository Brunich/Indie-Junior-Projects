extends Node

const BattleManager := preload("res://codigo/batalla/battle_manager.gd")
const CreatureInstance := preload("res://codigo/recursos/creature_instance.gd")
const ExperienceSystem := preload("res://codigo/batalla/experience_system.gd")

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	GameManager.clear_party()
	GameManager.flags = {}
	GameManager.caught_ids = []
	GameManager.seen_ids = []
	GameManager.storage_box.clear()

	var player := CreatureInstance.create("embral", 13)
	var growth := ExperienceSystem.get_growth_rate(player.creature_id)
	player.experience = ExperienceSystem.exp_for_level(14, growth) - 1
	GameManager.party = [player]

	var enemy := CreatureInstance.create("coylto", 1)
	var manager := BattleManager.new()
	add_child(manager)
	manager.player_creature = player
	manager.enemy_creature = enemy
	manager.move_replacement_requested.connect(func(_new_move: String, current_moves: Array[String]):
		if current_moves.size() != 4:
			push_error("move_forget_probe: la criatura no llego con 4 tecnicas")
			get_tree().quit()
			return
		manager.on_move_replacement_choice(0)
	)

	await manager._award_exp()

	if player.level != 14:
		push_error("move_forget_probe: no subio de nivel")
		get_tree().quit()
		return
	if player.moves.size() != 4:
		push_error("move_forget_probe: el moveset no quedo en 4")
		get_tree().quit()
		return
	if player.moves[0] == null or player.moves[0].move_name != "Fire Punch":
		push_error("move_forget_probe: no reemplazo la tecnica elegida")
		get_tree().quit()
		return
	for move in player.moves:
		if move != null and move.move_name == "Growl":
			push_error("move_forget_probe: la tecnica olvidada sigue presente")
			get_tree().quit()
			return

	print("MOVE_FORGET_PROBE ok level=%d moves=%s" % [player.level, str(player.moves.map(func(move): return move.move_name if move != null else "null"))])
	get_tree().quit()
