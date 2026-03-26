extends Node

const OVERWORLD_SCENE := preload("res://escenas/overworld/overworld.tscn")

var _unexpected_transition: bool = false

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	GameManager.setup_new_adventure("Luna", "embral")
	GameManager.pending_spawn_id = "nana_house_exit"
	GameManager.transition_requested.connect(_on_transition_requested)

	var overworld = OVERWORLD_SCENE.instantiate()
	add_child(overworld)

	var player_ok := await _wait_until(func(): return get_tree().get_first_node_in_group("local_player") != null, 3.0)
	if not player_ok:
		push_error("overworld_return_probe: no se instancio el jugador local")
		get_tree().quit()
		return

	await _settle_frames(30)
	if _unexpected_transition:
		push_error("overworld_return_probe: reentrada inmediata a una casa al volver al pueblo")
	else:
		print("OVERWORLD_RETURN_PROBE ok")
	get_tree().quit()

func _on_transition_requested(target_scene: String, spawn_id: String) -> void:
	if target_scene.find("nana_house") != -1 or target_scene.find("warden_post") != -1 or target_scene.find("east_house") != -1:
		_unexpected_transition = true
		print("OVERWORLD_RETURN_PROBE unexpected target=", target_scene, " spawn=", spawn_id)

func _wait_until(predicate: Callable, timeout_seconds: float) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < int(timeout_seconds * 1000.0):
		if predicate.call():
			return true
		await get_tree().process_frame
	return false

func _settle_frames(frame_count: int) -> void:
	for _i in range(frame_count):
		await get_tree().process_frame
