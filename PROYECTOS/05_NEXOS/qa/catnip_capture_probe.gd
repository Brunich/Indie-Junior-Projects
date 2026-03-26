extends Node

const BATTLE_SCENE := preload("res://escenas/batalla/battle_scene.tscn")
const CreatureInstance := preload("res://codigo/recursos/creature_instance.gd")
const MoveData := preload("res://codigo/recursos/move_data.gd")
const CatchSystem := preload("res://codigo/batalla/catch_system.gd")

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	seed(1337)
	var failed_attempt := CatchSystem.catnip_attempt(3, 20, 20, CreatureInstance.Status.NONE, 1.0, 70, 1)
	if bool(failed_attempt.get("caught", false)):
		push_error("catnip_capture_probe: la prueba de fallo basico salio atrapada")
		get_tree().quit()
		return

	GameManager.clear_party()
	GameManager.flags = {}
	GameManager.caught_ids = []
	GameManager.seen_ids = []
	GameManager.storage_box.clear()
	InventorySystem.set_snapshot({"catnip_royal": 2})
	GameManager.setup_new_adventure("Probe", "embral")
	InventorySystem.add_item("catnip_royal", 2)

	var enemy = CreatureInstance.create("folimp", 2)
	enemy.hp_cur = 1
	enemy.moves.clear()
	enemy.moves.append(MoveData.growl())
	enemy.moves_pp.clear()
	enemy.moves_pp.append(enemy.moves[0].pp_max)
	GameManager.start_wild_battle(enemy, self)

	var battle = BATTLE_SCENE.instantiate()
	add_child(battle)
	if battle.manager.battle_over.is_connected(battle._on_battle_over):
		battle.manager.battle_over.disconnect(battle._on_battle_over)
	await get_tree().create_timer(4.5).timeout
	if battle.manager.phase == battle.manager.Phase.PLAYER_TURN:
		await battle.manager.on_player_used_item("catnip_royal")
	await get_tree().create_timer(1.5).timeout
	print("CATNIP_CAPTURE_PROBE in_battle=%s party=%d caught=%s" % [
		str(GameManager.in_battle),
		GameManager.party.size(),
		str(GameManager.caught_ids)
	])
	get_tree().quit()
