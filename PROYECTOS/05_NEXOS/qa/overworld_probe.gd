extends Node

const OVERWORLD_SCENE := preload("res://escenas/overworld/overworld.tscn")
const NANA_HOUSE_SCENE := preload("res://escenas/overworld/nana_house.tscn")

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	GameManager.setup_new_adventure("Luna", "embral")
	var overworld = OVERWORLD_SCENE.instantiate()
	add_child(overworld)
	await _wait_until(func(): return get_tree().get_first_node_in_group("local_player") != null, 3.0)
	await get_tree().create_timer(2.6).timeout
	await _capture("probe_overworld_villa_brasa.png")
	overworld.queue_free()
	await _settle_frames(6)

	var interior = NANA_HOUSE_SCENE.instantiate()
	add_child(interior)
	await _wait_until(func(): return get_tree().get_first_node_in_group("local_player") != null, 3.0)
	await _capture("probe_nana_house.png")
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
