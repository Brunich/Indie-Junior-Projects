extends Node

const SaveSystem := preload("res://codigo/sistemas/save_system.gd")

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	GameManager.setup_new_adventure("Probe", "embral")
	GameManager.set_checkpoint("res://escenas/overworld/reynosa_clinic.tscn", "default")
	for creature in GameManager.party:
		creature.hp_cur = 0
	SaveSystem.delete_save()

	var result := GameManager.process_party_defeat()
	if String(result.get("scene", "")) != "res://escenas/overworld/reynosa_clinic.tscn":
		push_error("defeat_respawn_probe: la escena de respawn no coincide con el checkpoint")
		get_tree().quit()
		return
	if String(result.get("spawn_id", "")) != "default":
		push_error("defeat_respawn_probe: el spawn de respawn no coincide")
		get_tree().quit()
		return
	if GameManager.all_fainted():
		push_error("defeat_respawn_probe: el equipo siguio agotado tras el respawn")
		get_tree().quit()
		return
	if SaveSystem.save_exists():
		push_error("defeat_respawn_probe: la derrota no debe guardar la partida por si sola")
		get_tree().quit()
		return

	print("DEFEAT_RESPAWN_PROBE ok scene=%s spawn=%s" % [result.get("scene", ""), result.get("spawn_id", "")])
	get_tree().quit()
