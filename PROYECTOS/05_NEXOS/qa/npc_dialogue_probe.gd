extends Node

const OVERWORLD_SCENE := preload("res://escenas/overworld/overworld.tscn")

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	GameManager.setup_new_adventure("Luna", "embral")
	var overworld = OVERWORLD_SCENE.instantiate()
	add_child(overworld)

	var ready_ok := await _wait_until(func():
		return get_tree().get_first_node_in_group("local_player") != null \
			and overworld.get_node_or_null("npc_dona_elva") != null \
			and overworld.get_node_or_null("dialogue_box") != null
	, 3.0)
	if not ready_ok:
		push_error("npc_dialogue_probe: faltan nodos base")
		get_tree().quit()
		return

	var player = get_tree().get_first_node_in_group("local_player")
	var npc = overworld.get_node("npc_dona_elva")
	var dialogue_box = overworld.get_node("dialogue_box")

	npc._begin_interaction(player)
	await get_tree().process_frame

	if not GameManager.dialogue_active:
		push_error("npc_dialogue_probe: dialogue_active nunca se activo")
		get_tree().quit()
		return
	if not npc.get("_is_talking"):
		push_error("npc_dialogue_probe: NPC no quedo bloqueado durante el dialogo")
		get_tree().quit()
		return

	dialogue_box._end_dialogue()
	await get_tree().process_frame

	if GameManager.dialogue_active:
		push_error("npc_dialogue_probe: dialogue_active no se limpio")
		get_tree().quit()
		return
	if npc.get("_is_talking"):
		push_error("npc_dialogue_probe: NPC siguio bloqueado tras cerrar dialogo")
		get_tree().quit()
		return

	print("NPC_DIALOGUE_PROBE ok")
	get_tree().quit()

func _wait_until(predicate: Callable, timeout_seconds: float) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < int(timeout_seconds * 1000.0):
		if predicate.call():
			return true
		await get_tree().process_frame
	return false
