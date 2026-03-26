extends Node

const OVERWORLD_SCENE := preload("res://escenas/overworld/overworld.tscn")

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	GameManager.setup_new_adventure("Probe", "embral")
	var scene = OVERWORLD_SCENE.instantiate()
	add_child(scene)

	var ready_ok := await _wait_until(func():
		return scene.get_node_or_null("npc_brix") != null and get_tree().get_first_node_in_group("local_player") != null
	, 3.0)
	if not ready_ok:
		push_error("npc_wander_probe: no cargaron los nodos base")
		get_tree().quit()
		return

	var npc = scene.get_node("npc_brix")
	npc.set("_wander_dir", Vector2.RIGHT)
	npc.set("_wander_timer", 2.0)
	var before: Vector2 = npc.global_position
	await get_tree().create_timer(1.2).timeout
	var after: Vector2 = npc.global_position
	if npc.get("_wander_dir") == Vector2.RIGHT and after.distance_to(before) < 0.5:
		push_error("npc_wander_probe: el NPC siguio atorado sin reaccionar")
		get_tree().quit()
		return

	print("NPC_WANDER_PROBE ok dir=%s moved=%.2f" % [str(npc.get("_wander_dir")), after.distance_to(before)])
	get_tree().quit()

func _wait_until(predicate: Callable, timeout_seconds: float) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < int(timeout_seconds * 1000.0):
		if predicate.call():
			return true
		await get_tree().process_frame
	return false
