extends Node

const OVERWORLD_SCENE := preload("res://escenas/overworld/overworld.tscn")
const ROUTE_SCENE := preload("res://escenas/overworld/route1.tscn")
const CITY_SCENE := preload("res://escenas/overworld/ashgate.tscn")
const ROUTE2_SCENE := preload("res://escenas/overworld/route2.tscn")
const NEXT_CITY_SCENE := preload("res://escenas/overworld/valle_cempa.tscn")

var _village_area: int = 0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	call_deferred("_run")

func _run() -> void:
	GameManager.setup_new_adventure("Probe", "embral")
	await _probe_reynosa()
	await _probe_route()
	await _probe_monterrey()
	await _probe_route2()
	await _probe_valle_cempa()
	print("WORLD_PATH_PROBE ok area_base=", _village_area)
	get_tree().quit()

func _probe_reynosa() -> void:
	GameManager.pending_spawn_id = "north_route_entry"
	var scene = OVERWORLD_SCENE.instantiate()
	add_child(scene)

	var ready_ok := await _wait_until(func():
		return get_tree().get_first_node_in_group("local_player") != null and scene.get_node_or_null("VillageMap") != null
	, 3.0)
	if not ready_ok:
		push_error("world_path_probe: Reynosa no termino de cargar")
		get_tree().quit()
		return

	var player = get_tree().get_first_node_in_group("local_player")
	var map = scene.get_node("VillageMap")
	var expected: Vector2 = map.get_spawn_world_pos("north_route_entry")
	if player.global_position.distance_to(expected) > 1.5:
		push_error("world_path_probe: spawn norte de Reynosa mal alineado")
		get_tree().quit()
		return

	var warp = scene.get_node("warp_south")
	if warp.target_scene != "res://escenas/overworld/route1.tscn" or warp.target_spawn != "from_village":
		push_error("world_path_probe: salida de Reynosa mal configurada")
		get_tree().quit()
		return
	var warp_shape = warp.get_node("CollisionShape2D")
	if warp_shape.position.y > 80.0:
		push_error("world_path_probe: la salida de Reynosa no quedo arriba")
		get_tree().quit()
		return

	var limits: Rect2i = map.get_camera_limits()
	_village_area = limits.size.x * limits.size.y
	await _free_scene(scene)

func _probe_route() -> void:
	GameManager.pending_spawn_id = "from_village"
	var scene = ROUTE_SCENE.instantiate()
	add_child(scene)

	var ready_ok := await _wait_until(func():
		return get_tree().get_first_node_in_group("local_player") != null and scene.get_node_or_null("RouteMap") != null
	, 3.0)
	if not ready_ok:
		push_error("world_path_probe: la ruta no termino de cargar")
		get_tree().quit()
		return

	var player = get_tree().get_first_node_in_group("local_player")
	var map = scene.get_node("RouteMap")
	var bottom_spawn: Vector2 = map.get_spawn_world_pos("from_village")
	var top_spawn: Vector2 = map.get_spawn_world_pos("from_ashgate")
	if player.global_position.distance_to(bottom_spawn) > 1.5:
		push_error("world_path_probe: spawn sur de la ruta mal alineado")
		get_tree().quit()
		return
	if bottom_spawn.y <= top_spawn.y:
		push_error("world_path_probe: la ruta no quedo vertical de sur a norte")
		get_tree().quit()
		return

	var warp_back = scene.get_node("warp_back_village")
	var warp_city = scene.get_node("warp_ashgate")
	if warp_back.target_spawn != "north_route_entry":
		push_error("world_path_probe: regreso a Reynosa mal configurado")
		get_tree().quit()
		return
	if warp_city.target_scene != "res://escenas/overworld/ashgate.tscn" or warp_city.target_spawn != "from_route1":
		push_error("world_path_probe: salida norte de la ruta mal configurada")
		get_tree().quit()
		return
	await _free_scene(scene)

func _probe_monterrey() -> void:
	GameManager.pending_spawn_id = "from_route1"
	var scene = CITY_SCENE.instantiate()
	add_child(scene)

	var ready_ok := await _wait_until(func():
		return get_tree().get_first_node_in_group("local_player") != null and scene.get_node_or_null("RouteMap") != null
	, 3.0)
	if not ready_ok:
		push_error("world_path_probe: Monterrey no termino de cargar")
		get_tree().quit()
		return

	var player = get_tree().get_first_node_in_group("local_player")
	var map = scene.get_node("RouteMap")
	var expected: Vector2 = map.get_spawn_world_pos("from_route1")
	if player.global_position.distance_to(expected) > 1.5:
		push_error("world_path_probe: spawn de entrada a Monterrey mal alineado")
		get_tree().quit()
		return

	var limits: Rect2i = map.get_camera_limits()
	var city_area := limits.size.x * limits.size.y
	if city_area < int(_village_area * 3.7):
		push_error("world_path_probe: Monterrey no quedo suficientemente grande")
		get_tree().quit()
		return

	var warp_route = scene.get_node("warp_south_route1")
	if warp_route.target_scene != "res://escenas/overworld/route1.tscn" or warp_route.target_spawn != "from_ashgate":
		push_error("world_path_probe: regreso de Monterrey a la ruta mal configurado")
		get_tree().quit()
		return
	var warp_route2 = scene.get_node("warp_route2_east")
	if warp_route2.target_scene != "res://escenas/overworld/route2.tscn" or warp_route2.target_spawn != "from_ashgate":
		push_error("world_path_probe: salida oriente de Monterrey mal configurada")
		get_tree().quit()
		return
	await _free_scene(scene)

func _probe_route2() -> void:
	GameManager.pending_spawn_id = "from_ashgate"
	var scene = ROUTE2_SCENE.instantiate()
	add_child(scene)

	var ready_ok := await _wait_until(func():
		return get_tree().get_first_node_in_group("local_player") != null and scene.get_node_or_null("RouteMap") != null
	, 3.0)
	if not ready_ok:
		push_error("world_path_probe: la ruta 2 no termino de cargar")
		get_tree().quit()
		return

	var player = get_tree().get_first_node_in_group("local_player")
	var map = scene.get_node("RouteMap")
	var west_spawn: Vector2 = map.get_spawn_world_pos("from_ashgate")
	var east_spawn: Vector2 = map.get_spawn_world_pos("from_valle")
	if player.global_position.distance_to(west_spawn) > 1.5:
		push_error("world_path_probe: spawn poniente de la ruta 2 mal alineado")
		get_tree().quit()
		return
	if west_spawn.x >= east_spawn.x:
		push_error("world_path_probe: la ruta 2 no quedo como corredor de oeste a este")
		get_tree().quit()
		return

	var warp_back = scene.get_node("warp_west_ashgate")
	var warp_next = scene.get_node("warp_east_valle")
	if warp_back.target_scene != "res://escenas/overworld/ashgate.tscn" or warp_back.target_spawn != "from_route2":
		push_error("world_path_probe: regreso de la ruta 2 a Monterrey mal configurado")
		get_tree().quit()
		return
	if warp_next.target_scene != "res://escenas/overworld/valle_cempa.tscn" or warp_next.target_spawn != "from_route2":
		push_error("world_path_probe: salida oriente de la ruta 2 mal configurada")
		get_tree().quit()
		return
	await _free_scene(scene)

func _probe_valle_cempa() -> void:
	GameManager.pending_spawn_id = "from_route2"
	var scene = NEXT_CITY_SCENE.instantiate()
	add_child(scene)

	var ready_ok := await _wait_until(func():
		return get_tree().get_first_node_in_group("local_player") != null and scene.get_node_or_null("RouteMap") != null
	, 3.0)
	if not ready_ok:
		push_error("world_path_probe: Valle Cempa no termino de cargar")
		get_tree().quit()
		return

	var player = get_tree().get_first_node_in_group("local_player")
	var map = scene.get_node("RouteMap")
	var expected: Vector2 = map.get_spawn_world_pos("from_route2")
	if player.global_position.distance_to(expected) > 1.5:
		push_error("world_path_probe: spawn de entrada a Valle Cempa mal alineado")
		get_tree().quit()
		return

	var warp_back = scene.get_node("warp_back_route2")
	if warp_back.target_scene != "res://escenas/overworld/route2.tscn" or warp_back.target_spawn != "from_valle":
		push_error("world_path_probe: regreso de Valle Cempa a la ruta 2 mal configurado")
		get_tree().quit()
		return

	var warp_clinic = scene.get_node("warp_clinic")
	if warp_clinic.target_scene != "res://escenas/overworld/valle_cempa_clinic.tscn" or warp_clinic.target_spawn != "from_city":
		push_error("world_path_probe: acceso a la clinica de Valle Cempa mal configurado")
		get_tree().quit()
		return
	await _free_scene(scene)

func _wait_until(predicate: Callable, timeout_seconds: float) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < int(timeout_seconds * 1000.0):
		if predicate.call():
			return true
		await get_tree().process_frame
	return false

func _free_scene(scene: Node) -> void:
	if scene != null:
		scene.queue_free()
	await get_tree().process_frame
	await get_tree().process_frame
