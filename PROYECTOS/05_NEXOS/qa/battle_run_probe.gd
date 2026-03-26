extends Node

const BattleSceneScene := preload("res://escenas/batalla/battle_scene.tscn")
const CreatureInstance := preload("res://codigo/recursos/creature_instance.gd")

var _captured_scene: String = ""
var _captured_spawn: String = ""
var _battle_scene: Node = null

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	GameManager.transition_requested.connect(_on_transition_requested)
	call_deferred("_run")

func _run() -> void:
	GameManager.setup_new_adventure("Probe", "embral")
	GameManager.flags.erase("last_defeat")
	GameManager.save_scene = "res://escenas/overworld/route1.tscn"
	GameManager.save_position = Vector2(160, 544)
	GameManager.pending_spawn_id = ""

	var enemy := CreatureInstance.create("folimp", 4)
	GameManager.start_wild_battle(enemy, self)

	_battle_scene = BattleSceneScene.instantiate()
	add_child(_battle_scene)

	var ready_ok := await _wait_until(func():
		return _battle_scene.get_node("ui/move_menu").visible
	, 4.0)
	if not ready_ok:
		push_error("battle_run_probe: la batalla no llego al turno del jugador")
		await _finish()
		return

	_battle_scene.manager.on_player_ran()

	var escaped_ok := await _wait_until(func():
		return _captured_scene != ""
	, 3.0)
	if not escaped_ok:
		push_error("battle_run_probe: huir no solicito volver al mapa")
		await _finish()
		return

	if _captured_scene != GameManager.save_scene:
		push_error("battle_run_probe: la huida apunto a una escena equivocada")
		await _finish()
		return
	if _captured_spawn != "":
		push_error("battle_run_probe: la huida no debio forzar un spawn nuevo")
		await _finish()
		return
	if GameManager.save_position.distance_to(Vector2(160, 544)) > 0.01:
		push_error("battle_run_probe: la posicion guardada se altero al huir")
		await _finish()
		return
	if GameManager.flags.get("last_defeat", false):
		push_error("battle_run_probe: huir marco la pelea como derrota")
		await _finish()
		return

	print("BATTLE_RUN_PROBE ok escena=", _captured_scene, " pos=", GameManager.save_position)
	await _finish()

func _on_transition_requested(scene_path: String, spawn_id: String) -> void:
	if _captured_scene == "":
		_captured_scene = scene_path
		_captured_spawn = spawn_id

func _wait_until(predicate: Callable, timeout_seconds: float) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < int(timeout_seconds * 1000.0):
		if predicate.call():
			return true
		await get_tree().process_frame
	return false

func _finish() -> void:
	if GameManager.transition_requested.is_connected(_on_transition_requested):
		GameManager.transition_requested.disconnect(_on_transition_requested)
	if _battle_scene != null and is_instance_valid(_battle_scene):
		_battle_scene.queue_free()
		await get_tree().process_frame
		await get_tree().process_frame
	get_tree().quit()
