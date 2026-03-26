extends Node

const OVERWORLD_SCENE := preload("res://escenas/overworld/overworld.tscn")
const ROUTE_SCENE := preload("res://escenas/overworld/route1.tscn")

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	call_deferred("_run")

func _run() -> void:
	GameManager.setup_new_adventure("Probe", "embral")
	await _probe_city_without_encounters()
	await _probe_route_grass_only()
	print("GRASS_ONLY_PROBE ok")
	get_tree().quit()

func _probe_city_without_encounters() -> void:
	GameManager.in_battle = false
	var overworld = OVERWORLD_SCENE.instantiate()
	add_child(overworld)

	var ready_ok := await _wait_until(func():
		return get_tree().get_first_node_in_group("local_player") != null and overworld.get_node_or_null("OverworldController") != null
	, 3.0)
	if not ready_ok:
		push_error("grass_only_probe: Reynosa no cargo")
		get_tree().quit()
		return

	var player = get_tree().get_first_node_in_group("local_player")
	var controller = overworld.get_node("OverworldController")
	player.global_position = Vector2((8.5) * 16.0, (29.5) * 16.0)
	controller.set("_steps_to_encounter", 1)
	controller._on_player_stepped(1)
	await get_tree().process_frame

	if GameManager.in_battle:
		push_error("grass_only_probe: hubo encuentro dentro de Reynosa")
		get_tree().quit()
		return

	overworld.queue_free()
	await get_tree().process_frame
	await get_tree().process_frame

func _probe_route_grass_only() -> void:
	GameManager.in_battle = false
	var route = ROUTE_SCENE.instantiate()
	add_child(route)

	var ready_ok := await _wait_until(func():
		return get_tree().get_first_node_in_group("local_player") != null and route.get_node_or_null("OverworldController") != null
	, 3.0)
	if not ready_ok:
		push_error("grass_only_probe: la ruta no cargo")
		get_tree().quit()
		return

	var controller = route.get_node("OverworldController")
	var battle_cb := Callable(controller, "_on_battle_started")
	if GameManager.battle_started.is_connected(battle_cb):
		GameManager.battle_started.disconnect(battle_cb)

	var player = get_tree().get_first_node_in_group("local_player")
	player.global_position = Vector2(160, 780)
	controller.set("_steps_to_encounter", 1)
	controller._on_player_stepped(1)
	await get_tree().process_frame

	if GameManager.in_battle:
		push_error("grass_only_probe: hubo encuentro fuera del pasto")
		get_tree().quit()
		return

	var patch = route.get_node("TallGrassPatch")
	patch.encounter_rate = 1.0
	player.global_position = Vector2(160, 544)
	patch._on_body_entered(player)
	patch._try_encounter()
	await get_tree().process_frame

	if not GameManager.in_battle:
		push_error("grass_only_probe: no hubo encuentro dentro del pasto")
		get_tree().quit()
		return

	route.queue_free()
	await get_tree().process_frame
	await get_tree().process_frame

func _wait_until(predicate: Callable, timeout_seconds: float) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < int(timeout_seconds * 1000.0):
		if predicate.call():
			return true
		await get_tree().process_frame
	return false
