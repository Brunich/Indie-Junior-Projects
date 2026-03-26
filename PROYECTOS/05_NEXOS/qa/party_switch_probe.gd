extends Node

const GameMenuScene := preload("res://escenas/ui/game_menu.tscn")
const CreatureInstance := preload("res://codigo/recursos/creature_instance.gd")

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	call_deferred("_run")

func _run() -> void:
	GameManager.clear_party()
	GameManager.flags = {}
	GameManager.caught_ids = []
	GameManager.seen_ids = []
	GameManager.storage_box.clear()
	GameManager.setup_new_adventure("Probe", "embral")

	var reserve := CreatureInstance.create("folimp", 6)
	reserve.nickname = "Prueba"
	GameManager.add_to_party(reserve)

	var menu = GameMenuScene.instantiate()
	add_child(menu)
	await _settle_frames(4)
	menu.open_menu()
	await _settle_frames(6)

	var party_screen = menu.get_node("root_panel/layout/screens/party_screen")
	if GameManager.party.size() < 2:
		push_error("party_switch_probe: faltan criaturas para probar el cambio")
		get_tree().paused = false
		get_tree().quit()
		return

	var starter_id := String(GameManager.party[0].creature_id)
	var reserve_id := String(GameManager.party[1].creature_id)

	var down := InputEventAction.new()
	down.action = "ui_down"
	down.pressed = true
	party_screen._input(down)
	await _settle_frames(2)

	var accept := InputEventAction.new()
	accept.action = "ui_accept"
	accept.pressed = true
	party_screen._input(accept)
	await _settle_frames(4)

	if String(GameManager.party[0].creature_id) != reserve_id:
		push_error("party_switch_probe: el cambio por teclado no puso al frente la reserva")
		get_tree().paused = false
		get_tree().quit()
		return

	var slot_buttons: Array = party_screen.get("_slot_buttons")
	if slot_buttons.size() < 2:
		push_error("party_switch_probe: no se reconstruyeron los botones de slots")
		get_tree().paused = false
		get_tree().quit()
		return

	var second_button := slot_buttons[1] as Button
	second_button.emit_signal("pressed")
	await _settle_frames(2)
	var front_button := party_screen.get_node("summary_panel/btn_heal") as Button
	front_button.emit_signal("pressed")
	await _settle_frames(4)

	if String(GameManager.party[0].creature_id) != starter_id:
		push_error("party_switch_probe: el cambio por interfaz no devolvio al frente a la inicial")
		get_tree().paused = false
		get_tree().quit()
		return

	if not party_screen.get_node("summary_panel").visible:
		push_error("party_switch_probe: el panel de resumen se oculto tras el cambio")
		get_tree().paused = false
		get_tree().quit()
		return

	menu.close_menu()
	await _settle_frames(3)
	print("PARTY_SWITCH_PROBE ok frente=", GameManager.party[0].display_name())
	get_tree().paused = false
	get_tree().quit()

func _settle_frames(frame_count: int) -> void:
	for _i in range(frame_count):
		await get_tree().process_frame
