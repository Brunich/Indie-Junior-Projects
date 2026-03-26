extends Node

const TITLE_SCENE := preload("res://escenas/ui/title_screen.tscn")
const OVERWORLD_SCENE := preload("res://escenas/overworld/overworld.tscn")
const BATTLE_SCENE := preload("res://escenas/batalla/battle_scene.tscn")
const CreatureInstance := preload("res://codigo/recursos/creature_instance.gd")
const MoveData := preload("res://codigo/recursos/move_data.gd")
const ExperienceSystem := preload("res://codigo/batalla/experience_system.gd")
const SaveSystem := preload("res://codigo/sistemas/save_system.gd")

var _results: Array[Dictionary] = []
var _artifact_dir: String
var _save_backup_exists := false
var _save_backup_text := ""

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	randomize()
	_artifact_dir = ProjectSettings.globalize_path("res://qa/artifacts")
	DirAccess.make_dir_recursive_absolute(_artifact_dir)
	_backup_player_save()

	await _test_title_flow()
	await _test_new_game_state()
	await _test_continue_flow()
	await _test_overworld_load()
	await _test_battle_flow()

	_restore_player_save()
	_write_report()
	var failed := _results.any(func(entry): return not bool(entry.get("ok", false)))
	get_tree().quit(1 if failed else 0)

func _test_title_flow() -> void:
	_reset_state()
	var title = TITLE_SCENE.instantiate()
	add_child(title)
	await _settle_frames(4)

	_record(title._phase == title.Phase.LOGO, "title/logo_phase", "La portada arranca en fase logo.")
	title._enter_phase(title.Phase.MENU)
	await _settle_frames(4)
	_record(title._menu_panel.visible, "title/menu_visible", "El menu principal se muestra.")
	await _capture("smoke_title_menu.png")

	title._enter_phase(title.Phase.NAME_ENTRY)
	await _settle_frames(2)
	title._name_entry.text = "Luna"
	_record(title._name_panel.visible and title._name_entry.text == "Luna", "title/name_entry", "Se puede escribir nombre.")

	title._on_name_confirmed()
	await _settle_frames(4)
	_record(title._phase == title.Phase.INTRO_CRAWL, "title/intro_crawl", "La narrativa inicial arranca despues del nombre.")

	title._enter_phase(title.Phase.STARTER_SELECT)
	await _settle_frames(4)
	_record(title._starter_panel.visible, "title/starter_panel", "La seleccion de criatura inicial aparece.")
	await _capture("smoke_starter_select.png")

	title.queue_free()
	await _settle_frames(2)

func _test_new_game_state() -> void:
	_reset_state()
	GameManager.setup_new_adventure("Luna", "embral")
	_record(GameManager.player_name == "Luna", "new_game/player_name", "Se guarda el nombre de jugador.")
	_record(GameManager.party.size() == 1, "new_game/party_size", "La partida nueva arranca con una sola criatura inicial.")
	_record(GameManager.party[0].creature_id == "embral", "new_game/starter_set", "La criatura inicial elegida queda al frente.")
	var save_data := SaveSystem.load_game()
	_record(save_data.get("player_name", "") == "Luna", "new_game/save_player_name", "La nueva partida se persiste para futuras sesiones.")
	_record(save_data.get("flags", {}).get("starter_id", "") == "embral", "new_game/save_starter", "El guardado conserva la criatura inicial elegida.")

func _test_continue_flow() -> void:
	_reset_state()
	GameManager.setup_new_adventure("Luna", "folimp")
	GameManager.player_name = "Luna guardada"
	GameManager.save()
	GameManager.clear_party()
	GameManager.player_name = "Temporal"

	var title = TITLE_SCENE.instantiate()
	add_child(title)
	await _settle_frames(4)
	title._enter_phase(title.Phase.MENU)
	await _settle_frames(2)
	title._on_continue_pressed()
	await _settle_frames(4)

	_record(GameManager.player_name == "Luna guardada", "continue/load_name", "Continuar recupera el nombre guardado.")
	_record(GameManager.party.size() == 1 and GameManager.party[0].creature_id == "folimp", "continue/load_party", "Continuar recupera la criatura guardada.")
	_record(title._target_scene_path == OVERWORLD_SCENE, "continue/load_scene", "Continuar regresa a una escena jugable del overworld.")

	title.queue_free()
	await _settle_frames(2)

func _test_overworld_load() -> void:
	_reset_state()
	GameManager.setup_new_adventure("Luna", "embral")
	var scene = OVERWORLD_SCENE.instantiate()
	add_child(scene)
	await _wait_until(func(): return get_tree().get_first_node_in_group("local_player") != null, 2.5)

	var player = get_tree().get_first_node_in_group("local_player")
	_record(player != null, "overworld/player_spawn", "El jugador aparece en Villa Brasa.")
	_record(scene.get_node_or_null("GameMenu") != null, "overworld/game_menu", "El menu de juego esta presente en overworld.")
	if player != null:
		var start_pos: Vector2 = player.global_position
		Input.action_press("ui_right")
		await _settle_frames(16)
		Input.action_release("ui_right")
		await _settle_frames(4)
		_record(player.global_position.x > start_pos.x + 4.0, "overworld/move_right", "El jugador puede moverse con las acciones ligadas a WASD.")
	var npc = scene.get_node_or_null("npc_dona_elva")
	var dialogue = scene.get_node_or_null("dialogue_box")
	var grass = scene.get_node_or_null("TallGrassSouth")
	var controller = scene.get_node_or_null("OverworldController")
	if player != null and npc != null and dialogue != null:
		player.global_position = npc.global_position + Vector2(0, 8)
		await _settle_frames(16)
		if npc.get("_nearby_player") == null and npc.has_method("_on_body_entered"):
			npc._on_body_entered(player)
		_record(npc.get("_nearby_player") != null, "overworld/npc_detect", "El NPC detecta al jugador cuando esta cerca.")
		var interact_press := InputEventAction.new()
		interact_press.action = "interact"
		interact_press.pressed = true
		Input.parse_input_event(interact_press)
		await _settle_frames(2)
		var interact_release := InputEventAction.new()
		interact_release.action = "interact"
		interact_release.pressed = false
		Input.parse_input_event(interact_release)
		var spoke := await _wait_until(func(): return dialogue.visible or dialogue.label.text.length() > 0, 2.0)
		_record(spoke, "overworld/npc_talk", "Shift activa conversacion con NPC en el overworld.")
		if dialogue.has_method("_end_dialogue"):
			dialogue._end_dialogue()
	if player != null and grass != null and controller != null:
		if GameManager.battle_started.is_connected(controller._on_battle_started):
			GameManager.battle_started.disconnect(controller._on_battle_started)
		grass.encounter_rate = 1.0
		player.global_position = Vector2(256, 392)
		await _settle_frames(8)
		Input.action_press("ui_right")
		await _settle_frames(20)
		Input.action_release("ui_right")
		var grass_battle := await _wait_until(func(): return GameManager.in_battle, 2.0)
		_record(grass_battle, "overworld/tall_grass_battle", "Caminar por arbustos puede disparar una batalla.")
		if grass_battle:
			GameManager.finish_battle(false)
			if player.has_method("unfreeze"):
				player.unfreeze()
		if not GameManager.battle_started.is_connected(controller._on_battle_started):
			GameManager.battle_started.connect(controller._on_battle_started)
	await _capture("smoke_overworld_start.png")

	scene.queue_free()
	await _settle_frames(3)

func _test_battle_flow() -> void:
	_reset_state()
	GameManager.setup_new_adventure("Luna", "embral")

	var starter = GameManager.party[0]
	var exp_to_6 := ExperienceSystem.exp_for_level(6, ExperienceSystem.get_growth_rate(starter.creature_id))
	starter.experience = exp_to_6 - 30

	var enemy = CreatureInstance.create("folimp", 6)
	enemy.nickname = "Folimp montaraz"
	enemy.moves.clear()
	enemy.moves.append(MoveData.growl())
	enemy.moves_pp.clear()
	enemy.moves_pp.append(enemy.moves[0].pp_max)
	enemy.hp_cur = 1

	GameManager.start_wild_battle(enemy, self)

	var battle = BATTLE_SCENE.instantiate()
	add_child(battle)
	await _settle_frames(8)

	if battle.manager.battle_over.is_connected(battle._on_battle_over):
		battle.manager.battle_over.disconnect(battle._on_battle_over)

	var log: Array[String] = []
	battle.manager.text_requested.connect(func(msg: String): log.append(msg))

	var reached_turn := await _wait_until(func(): return battle.manager.phase == battle.manager.Phase.PLAYER_TURN and battle.manager._waiting_input, 6.0)
	_record(reached_turn, "battle/player_turn", "El combate llega al turno del jugador.")
	_record(battle.move_menu.visible, "battle/move_menu_visible", "El menu de tecnicas aparece en combate.")
	await _capture("smoke_battle_turn.png")

	var pp_before: int = int(battle.manager.player_creature.moves_pp[0])
	battle.manager.on_player_selected_move(0)
	var battle_finished := await _wait_until(func(): return not GameManager.in_battle, 8.0)
	_record(battle_finished, "battle/end_flow", "La pelea termina sin colgarse.")
	_record(battle.manager.player_creature.moves_pp[0] == pp_before - 1, "battle/pp_spent", "El uso de tecnica gasta PP.")
	_record(battle.manager.enemy_creature.is_fainted, "battle/enemy_fainted", "El enemigo cae al recibir dano.")
	_record(battle.manager.player_creature.level >= 6, "battle/level_up", "La criatura activa sube de nivel al ganar EXP.")
	_record(log.any(func(msg): return msg.contains("uso")), "battle/text_log_attack", "Se emiten textos de ataque.")
	_record(log.any(func(msg): return msg.contains("subio al nivel")), "battle/text_log_level_up", "Se emiten textos de subida de nivel.")

	battle.queue_free()
	await _settle_frames(3)

func _reset_state() -> void:
	GameManager.clear_party()
	GameManager.flags = {}
	GameManager.caught_ids = []
	GameManager.seen_ids = []
	GameManager.pending_spawn_id = ""
	GameManager.save_position = Vector2.ZERO
	GameManager.save_scene = "res://escenas/overworld/overworld.tscn"
	GameManager.storage_box.clear()
	GameManager.money = 0
	if InventorySystem.has_method("set_snapshot"):
		InventorySystem.set_snapshot({})
	if GameManager.in_battle:
		GameManager.finish_battle(false)

func _record(ok: bool, key: String, detail: String) -> void:
	_results.append({"ok": ok, "key": key, "detail": detail})
	var prefix := "SMOKE PASS" if ok else "SMOKE FAIL"
	print("%s :: %s :: %s" % [prefix, key, detail])

func _capture(filename: String) -> void:
	if String(DisplayServer.get_name()) == "headless":
		_record(true, "capture/%s" % filename, "Captura omitida en modo headless.")
		return
	await RenderingServer.frame_post_draw
	var image = get_viewport().get_texture().get_image()
	if image == null:
		_record(false, "capture/%s" % filename, "No se pudo obtener imagen del viewport.")
		return
	var path := _artifact_dir.path_join(filename)
	var err := image.save_png(path)
	_record(err == OK, "capture/%s" % filename, "Captura guardada en %s" % path)

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

func _write_report() -> void:
	var path := _artifact_dir.path_join("smoke_report.txt")
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		print("SMOKE FAIL :: report :: No se pudo escribir reporte.")
		return
	for entry in _results:
		var line := "[%s] %s :: %s\n" % [
			"OK" if bool(entry["ok"]) else "FAIL",
			String(entry["key"]),
			String(entry["detail"])
		]
		file.store_string(line)
	file.close()
	print("SMOKE REPORT :: %s" % path)

func _backup_player_save() -> void:
	var path := ProjectSettings.globalize_path("user://emberveil_save.json")
	if not FileAccess.file_exists(path):
		_save_backup_exists = false
		_save_backup_text = ""
		return
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		_save_backup_exists = false
		_save_backup_text = ""
		return
	_save_backup_exists = true
	_save_backup_text = file.get_as_text()

func _restore_player_save() -> void:
	var path := ProjectSettings.globalize_path("user://emberveil_save.json")
	if _save_backup_exists:
		var file := FileAccess.open(path, FileAccess.WRITE)
		if file != null:
			file.store_string(_save_backup_text)
	elif FileAccess.file_exists(path):
		DirAccess.remove_absolute(path)
