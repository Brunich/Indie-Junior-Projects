extends Node

const BATTLE_SCENE := preload("res://escenas/batalla/battle_scene.tscn")
const CreatureInstance := preload("res://codigo/recursos/creature_instance.gd")
const MoveData := preload("res://codigo/recursos/move_data.gd")

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	GameManager.clear_party()
	GameManager.flags = {}
	GameManager.caught_ids = []
	GameManager.seen_ids = []
	InventorySystem.set_snapshot({"catnip_street": 3, "potion": 1})
	GameManager.setup_new_adventure("Probe", "embral")
	var enemy = CreatureInstance.create("folimp", 4)
	enemy.moves.clear()
	enemy.moves.append(MoveData.growl())
	enemy.moves_pp.clear()
	enemy.moves_pp.append(enemy.moves[0].pp_max)
	GameManager.start_wild_battle(enemy, self)
	var battle = BATTLE_SCENE.instantiate()
	add_child(battle)
	await get_tree().create_timer(5.0).timeout
	print("BATTLE_TURN_PROBE phase=%s waiting=%s move_menu=%s text=%s" % [
		str(battle.manager.phase),
		str(battle.manager._waiting_input),
		str(battle.move_menu.visible),
		battle.text_box.text
	])
	get_tree().quit()
