extends Node

const IMPORTED_SCENE := preload("res://escenas/overworld/reynosa_imported_demo.tscn")

var _transition_logged := false
var _scene_instance: Node = null

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	GameManager.setup_new_adventure("Importada", "embral")
	GameManager.transition_requested.connect(_on_transition_requested, CONNECT_ONE_SHOT)
	_scene_instance = IMPORTED_SCENE.instantiate()
	add_child(_scene_instance)

	var map_ready := await _wait_until(func():
		return _scene_instance.get_node_or_null("StaticMap") != null and get_tree().get_first_node_in_group("local_player") != null
	, 3.0)
	if not map_ready:
		push_error("imported_map_probe: no cargo el mapa importado")
		await _finish()
		return

	var map = _scene_instance.get_node("StaticMap")
	if map.get_node_or_null("Spawns/default") == null:
		push_error("imported_map_probe: faltan spawns importados")
		await _finish()
		return
	if map.get_node_or_null("WalkableZones/plaza_baja") == null:
		push_error("imported_map_probe: faltan zonas caminables importadas")
		await _finish()
		return
	if map.get_node_or_null("WarpZones/entrada_casa") == null:
		push_error("imported_map_probe: faltan warps importados")
		await _finish()
		return
	if map.get_node_or_null("NPCs/guardia_borde") == null:
		push_error("imported_map_probe: faltan NPCs importados")
		await _finish()
		return
	if map.get_node_or_null("EncounterZones") == null:
		push_error("imported_map_probe: faltan zonas de encuentro importadas")
		await _finish()
		return

	var player = get_tree().get_first_node_in_group("local_player")
	player.global_position = Vector2(644, 524)
	await _settle_frames(16)
	if not _transition_logged:
		push_error("imported_map_probe: el warp importado no disparo la transicion")
		await _finish()

func _on_transition_requested(target_scene: String, spawn_id: String) -> void:
	_transition_logged = true
	print("IMPORTED_MAP_PROBE target=%s spawn=%s" % [target_scene, spawn_id])
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
	if _scene_instance != null and is_instance_valid(_scene_instance):
		_scene_instance.queue_free()
		await get_tree().process_frame
		await get_tree().process_frame
	get_tree().quit()
