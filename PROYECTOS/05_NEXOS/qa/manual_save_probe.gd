extends Node

const SaveSystem := preload("res://codigo/sistemas/save_system.gd")

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	SaveSystem.delete_save()
	GameManager.setup_new_adventure("Manual", "embral")
	if SaveSystem.save_exists():
		push_error("manual_save_probe: la nueva partida no debe guardarse sola")
		get_tree().quit()
		return

	GameManager.save_scene = "res://escenas/overworld/route1.tscn"
	GameManager.save_position = Vector2(448, 608)
	GameManager.pending_spawn_id = "from_village"
	GameManager.set_checkpoint("res://escenas/overworld/reynosa_clinic.tscn", "default", Vector2(512, 768))
	GameManager.party[0].hp_cur = max(1, GameManager.party[0].hp_max - 7)
	InventorySystem.set_snapshot({
		"catnip_street": 5,
		"catnip_field": 2,
		"potion": 1,
	})

	if not GameManager.manual_save():
		push_error("manual_save_probe: fallo el guardado manual")
		get_tree().quit()
		return
	if not SaveSystem.save_exists():
		push_error("manual_save_probe: no se creo el archivo manual")
		get_tree().quit()
		return

	GameManager.player_name = "Mutada"
	GameManager.party[0].hp_cur = GameManager.party[0].hp_max
	InventorySystem.set_snapshot({})
	GameManager.save_scene = ""
	GameManager.save_position = Vector2.ZERO
	GameManager.pending_spawn_id = ""

	if not GameManager.load_save_file():
		push_error("manual_save_probe: no se pudo cargar el archivo manual")
		get_tree().quit()
		return

	if GameManager.player_name != "Manual":
		push_error("manual_save_probe: no se restauro el nombre del jugador")
		get_tree().quit()
		return
	if GameManager.save_scene != "res://escenas/overworld/route1.tscn":
		push_error("manual_save_probe: no se restauro la escena guardada")
		get_tree().quit()
		return
	if GameManager.save_position.distance_to(Vector2(448, 608)) > 0.01:
		push_error("manual_save_probe: no se restauro la posicion guardada")
		get_tree().quit()
		return
	if GameManager.party[0].hp_cur != GameManager.party[0].hp_max - 7:
		push_error("manual_save_probe: no se restauro el HP del equipo")
		get_tree().quit()
		return
	var snapshot := InventorySystem.get_snapshot()
	if int(snapshot.get("catnip_field", 0)) != 2 or int(snapshot.get("catnip_street", 0)) != 5:
		push_error("manual_save_probe: no se restauro el inventario")
		get_tree().quit()
		return

	SaveSystem.delete_save()
	print("MANUAL_SAVE_PROBE ok scene=%s pos=%s" % [GameManager.save_scene, GameManager.save_position])
	get_tree().quit()
