extends SceneTree

const BattleManager := preload("res://codigo/batalla/battle_manager.gd")
const CreatureInstance := preload("res://codigo/recursos/creature_instance.gd")
const MoveData := preload("res://codigo/recursos/move_data.gd")

func _gm() -> Node:
	return root.get_node("/root/GameManager")

func _inv() -> Node:
	return root.get_node("/root/InventorySystem")

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var game_manager := _gm()
	var inventory_system := _inv()
	game_manager.clear_party()
	game_manager.flags = {}
	game_manager.caught_ids = []
	game_manager.seen_ids = []
	game_manager.storage_box.clear()
	game_manager.setup_new_adventure("Probe", "embral")
	inventory_system.set_snapshot({"potion": 2})

	var reserve := CreatureInstance.create("folimp", 5)
	reserve.hp_cur = max(1, reserve.hp_max - 14)
	var reserve_hp_before := reserve.hp_cur
	game_manager.add_to_party(reserve)

	var enemy := CreatureInstance.create("coylto", 4)
	enemy.moves.clear()
	enemy.moves.append(MoveData.growl())
	enemy.moves_pp.clear()
	enemy.moves_pp.append(enemy.moves[0].pp_max)

	var manager := BattleManager.new()
	root.add_child(manager)
	manager.player_creature = game_manager.party[0]
	manager.enemy_creature = enemy
	manager.phase = manager.Phase.PLAYER_TURN
	manager._waiting_input = true

	manager.on_player_used_item("potion", 1)
	await create_timer(2.2).timeout
	if game_manager.party[1].hp_cur <= reserve_hp_before:
		push_error("exec_battle_item_target_probe: la reserva no recibio curacion")
		quit(1)
		return
	if inventory_system.get_quantity("potion") != 1:
		push_error("exec_battle_item_target_probe: no se consumio la pocion correcta")
		quit(1)
		return
	if manager.phase != manager.Phase.PLAYER_TURN or not manager._waiting_input:
		push_error("exec_battle_item_target_probe: no regreso el turno tras el uso valido")
		quit(1)
		return

	var lead_before: int = game_manager.party[0].hp_cur
	manager.on_player_used_item("potion", 0)
	await create_timer(1.6).timeout
	if inventory_system.get_quantity("potion") != 1:
		push_error("exec_battle_item_target_probe: un uso invalido consumio el objeto")
		quit(1)
		return
	if game_manager.party[0].hp_cur != lead_before:
		push_error("exec_battle_item_target_probe: la criatura activa cambio con objeto invalido")
		quit(1)
		return
	if manager.phase != manager.Phase.PLAYER_TURN or not manager._waiting_input:
		push_error("exec_battle_item_target_probe: el uso invalido no regreso el turno")
		quit(1)
		return

	print("EXEC_BATTLE_ITEM_TARGET_PROBE ok reserve_hp=%d potions=%d" % [
		game_manager.party[1].hp_cur,
		inventory_system.get_quantity("potion"),
	])
	quit()
