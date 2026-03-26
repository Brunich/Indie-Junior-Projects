extends Node

const REYNOSA_SCENE := preload("res://escenas/overworld/overworld.tscn")
const ROUTE_SCENE := preload("res://escenas/overworld/route1.tscn")
const MONTERREY_SCENE := preload("res://escenas/overworld/ashgate.tscn")

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	GameManager.setup_new_adventure("Luna", "embral")
	var reynosa = REYNOSA_SCENE.instantiate()
	add_child(reynosa)
	await _wait_until(func(): return get_tree().get_first_node_in_group("local_player") != null, 3.0)
	await get_tree().create_timer(2.2).timeout
	await _capture("probe_reynosa_map.png")
	reynosa.queue_free()
	await _settle_frames(6)

	GameManager.pending_spawn_id = "from_village"
	var route = ROUTE_SCENE.instantiate()
	add_child(route)
	await _wait_until(func(): return get_tree().get_first_node_in_group("local_player") != null, 3.0)
	await get_tree().create_timer(2.2).timeout
	await _capture("probe_route_vertical.png")
	route.queue_free()
	await _settle_frames(6)

	GameManager.pending_spawn_id = "from_route1"
	var monterrey = MONTERREY_SCENE.instantiate()
	add_child(monterrey)
	await _wait_until(func(): return get_tree().get_first_node_in_group("local_player") != null, 3.0)
	await get_tree().create_timer(2.2).timeout
	await _capture("probe_monterrey_map.png")
	get_tree().quit()

func _capture(filename: String) -> void:
	if String(DisplayServer.get_name()) == "headless":
		return
	await RenderingServer.frame_post_draw
	var image = get_viewport().get_texture().get_image()
	if image == null:
		return
	var dir := ProjectSettings.globalize_path("res://qa/artifacts")
	DirAccess.make_dir_recursive_absolute(dir)
	image.save_png(dir.path_join(filename))

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
