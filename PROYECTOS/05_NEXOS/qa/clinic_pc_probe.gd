extends Node

const CLINIC_SCENE := preload("res://escenas/overworld/reynosa_clinic.tscn")
const CreatureInstance := preload("res://codigo/recursos/creature_instance.gd")

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	GameManager.setup_new_adventure("Probe", "embral")
	GameManager.storage_box.clear()
	var extra := CreatureInstance.create("folimp", 4)
	GameManager.party.append(extra)
	GameManager.party[0].hp_cur = 1
	GameManager.party[1].hp_cur = 0

	var scene = CLINIC_SCENE.instantiate()
	add_child(scene)
	await get_tree().process_frame

	var menu = scene.get_node_or_null("CityServiceMenu")
	if menu == null:
		push_error("clinic_pc_probe: no se encontro el menu de clinica")
		get_tree().quit()
		return

	menu.open_service("pokecenter", {
		"title": "Clinica de prueba",
		"greeting": "Chequeo local",
		"checkpoint_scene": "res://escenas/overworld/reynosa_clinic.tscn",
		"checkpoint_spawn": "default",
	})
	menu._heal_party()

	if GameManager.party[0].hp_cur != GameManager.party[0].hp_max or GameManager.party[1].hp_cur != GameManager.party[1].hp_max:
		push_error("clinic_pc_probe: la curacion no dejo el equipo entero")
		get_tree().quit()
		return
	if GameManager.checkpoint_scene != "res://escenas/overworld/reynosa_clinic.tscn":
		push_error("clinic_pc_probe: la clinica no actualizo el checkpoint")
		get_tree().quit()
		return

	menu.open_service("pc", {"title": "PC local", "greeting": "Chequeo"})
	menu._deposit_creature(1)
	if GameManager.storage_box.is_empty():
		push_error("clinic_pc_probe: no pudo depositar a la caja")
		get_tree().quit()
		return
	menu._withdraw_creature(0)
	if GameManager.party.size() < 2:
		push_error("clinic_pc_probe: no pudo devolver la criatura al equipo")
		get_tree().quit()
		return

	print("CLINIC_PC_PROBE ok party=%d storage=%d" % [GameManager.party.size(), GameManager.storage_box.size()])
	get_tree().quit()
