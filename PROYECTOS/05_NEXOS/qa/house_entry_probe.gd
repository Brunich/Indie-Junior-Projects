extends Node

const NANA_HOUSE_SCENE := preload("res://escenas/overworld/nana_house.tscn")

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	GameManager.setup_new_adventure("Luna", "embral")
	GameManager.pending_spawn_id = "from_village"
	var interior = NANA_HOUSE_SCENE.instantiate()
	add_child(interior)

	var player_ok := await _wait_until(func(): return get_tree().get_first_node_in_group("local_player") != null, 3.0)
	if not player_ok:
		push_error("house_entry_probe: no se instancio el jugador local en nana_house")
		get_tree().quit()
		return

	await _settle_frames(40)
	var current_scene_path := ""
	if get_tree().current_scene:
		current_scene_path = get_tree().current_scene.scene_file_path
	print("HOUSE_ENTRY_PROBE scene=", current_scene_path if current_scene_path != "" else "manual_root")

	await _capture("probe_nana_house_entry.png")
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
