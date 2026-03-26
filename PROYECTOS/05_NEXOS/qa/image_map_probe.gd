extends Node

const STATIC_SCENE := preload("res://escenas/overworld/reynosa_static_demo.tscn")

var _transition_logged := false

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	GameManager.setup_new_adventure("Luna", "embral")
	GameManager.transition_requested.connect(_on_transition_requested, CONNECT_ONE_SHOT)
	var scene := STATIC_SCENE.instantiate()
	add_child(scene)
	var player_ok := await _wait_until(func(): return get_tree().get_first_node_in_group("local_player") != null, 3.0)
	if not player_ok:
		push_error("image_map_probe: no se instancio el jugador local")
		get_tree().quit()
		return
	var player := get_tree().get_first_node_in_group("local_player")
	player.global_position = Vector2(644, 524)
	await _settle_frames(16)
	if not _transition_logged:
		push_error("image_map_probe: no se disparo el warp del mapa por imagen")
		get_tree().quit()

func _on_transition_requested(target_scene: String, spawn_id: String) -> void:
	_transition_logged = true
	print("IMAGE_MAP_PROBE target=", target_scene, " spawn=", spawn_id)
	get_tree().quit()

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

