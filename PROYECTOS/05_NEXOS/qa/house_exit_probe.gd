extends Node

const NANA_HOUSE_SCENE := preload("res://escenas/overworld/nana_house.tscn")

var _transition_logged: bool = false
var _interior: Node = null

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	GameManager.setup_new_adventure("Luna", "embral")
	GameManager.pending_spawn_id = "from_village"
	GameManager.transition_requested.connect(_on_transition_requested, CONNECT_ONE_SHOT)

	_interior = NANA_HOUSE_SCENE.instantiate()
	add_child(_interior)

	var player_ok := await _wait_until(func(): return get_tree().get_first_node_in_group("local_player") != null, 3.0)
	if not player_ok:
		push_error("house_exit_probe: no se instancio el jugador local")
		await _finish()
		return

	var player := get_tree().get_first_node_in_group("local_player")
	player.global_position = Vector2(160, 196)
	await _settle_frames(12)
	if not is_inside_tree():
		return

	if not _transition_logged:
		push_error("house_exit_probe: no se disparo la salida a overworld")
	await _finish()

func _on_transition_requested(target_scene: String, spawn_id: String) -> void:
	_transition_logged = true
	print("HOUSE_EXIT_PROBE target=", target_scene, " spawn=", spawn_id)
	await _finish()

func _wait_until(predicate: Callable, timeout_seconds: float) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < int(timeout_seconds * 1000.0):
		if predicate.call():
			return true
		await get_tree().process_frame
	return false

func _settle_frames(frame_count: int) -> void:
	for _i in range(frame_count):
		if not is_inside_tree():
			return
		await get_tree().process_frame

func _finish() -> void:
	if _interior != null and is_instance_valid(_interior):
		_interior.queue_free()
		await get_tree().process_frame
		await get_tree().process_frame
	get_tree().quit()
