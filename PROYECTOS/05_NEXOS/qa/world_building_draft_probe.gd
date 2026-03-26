extends Node

const DRAFT_SCENE := preload("res://escenas/overworld/world_building_draft_demo.tscn")

var _transition_logged := false

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	GameManager.setup_new_adventure("Draft", "embral")
	GameManager.pending_spawn_id = "default"
	GameManager.transition_requested.connect(_on_transition_requested, CONNECT_ONE_SHOT)

	var scene = DRAFT_SCENE.instantiate()
	add_child(scene)

	var loaded := await _wait_until(func():
		return scene.get_node_or_null("StaticMap") != null and get_tree().get_first_node_in_group("local_player") != null
	, 3.0)
	if not loaded:
		push_error("world_building_draft_probe: no cargo la escena draft")
		get_tree().quit()
		return

	var map = scene.get_node("StaticMap")
	if map.get_node_or_null("WalkableZones/zona_principal") == null:
		push_error("world_building_draft_probe: faltan zonas caminables")
		get_tree().quit()
		return
	if map.get_node_or_null("WarpZones/entrada_casa_a") == null:
		push_error("world_building_draft_probe: falta warp de casa")
		get_tree().quit()
		return
	if map.get_node_or_null("WarpZones/salida_norte") == null:
		push_error("world_building_draft_probe: falta warp norte")
		get_tree().quit()
		return

	var player = get_tree().get_first_node_in_group("local_player")
	player.global_position = Vector2(248, 266)
	await _settle_frames(16)
	if not _transition_logged:
		push_error("world_building_draft_probe: el warp del draft no disparo transicion")
		get_tree().quit()

func _on_transition_requested(target_scene: String, spawn_id: String) -> void:
	_transition_logged = true
	print("WORLD_BUILDING_DRAFT_PROBE target=%s spawn=%s" % [target_scene, spawn_id])
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
