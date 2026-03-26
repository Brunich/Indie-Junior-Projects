extends Node

const BattleManager := preload("res://codigo/batalla/battle_manager.gd")
const CreatureInstance := preload("res://codigo/recursos/creature_instance.gd")
const MoveData := preload("res://codigo/recursos/move_data.gd")

var _manager: BattleManager = null

func _ready() -> void:
	print("BATTLE_ITEM_TARGET_PROBE ready")
	call_deferred("_run")

func _run() -> void:
	GameManager.clear_party()
	GameManager.flags = {}
	GameManager.caught_ids = []
	GameManager.seen_ids = []
	GameManager.storage_box.clear()
	GameManager.setup_new_adventure("Probe", "embral")
	InventorySystem.set_snapshot({"potion": 2})

	var reserve := CreatureInstance.create("folimp", 5)
	reserve.hp_cur = max(1, reserve.hp_max - 14)
	var reserve_hp_before: int = reserve.hp_cur
	GameManager.add_to_party(reserve)

	var enemy := CreatureInstance.create("coylto", 4)
	enemy.moves.clear()
	enemy.moves.append(MoveData.growl())
	enemy.moves_pp.clear()
	enemy.moves_pp.append(enemy.moves[0].pp_max)

	_manager = BattleManager.new()
	add_child(_manager)
	_manager.player_creature = GameManager.party[0]
	_manager.enemy_creature = enemy
	_manager.phase = _manager.Phase.PLAYER_TURN
	_manager._waiting_input = true

	_manager.on_player_used_item("potion", 1)
	var turn_returned_ok := await _wait_until(func():
		return _manager.phase == _manager.Phase.PLAYER_TURN and _manager._waiting_input
	, 4.5)
	if not turn_returned_ok:
		push_error("battle_item_target_probe: el turno valido nunca regreso al jugador")
		await _finish()
		return
	if GameManager.party[1].hp_cur <= reserve_hp_before:
		push_error("battle_item_target_probe: la reserva no recibio curacion")
		await _finish()
		return
	if InventorySystem.get_quantity("potion") != 1:
		push_error("battle_item_target_probe: no se consumio la pocion correcta")
		await _finish()
		return
	if _manager.phase != _manager.Phase.PLAYER_TURN or not _manager._waiting_input:
		push_error("battle_item_target_probe: no regreso el turno tras el uso valido")
		await _finish()
		return

	var lead_before: int = GameManager.party[0].hp_cur
	_manager.on_player_used_item("potion", 0)
	var invalid_returned_ok := await _wait_until(func():
		return _manager.phase == _manager.Phase.PLAYER_TURN and _manager._waiting_input
	, 2.5)
	if not invalid_returned_ok:
		push_error("battle_item_target_probe: el uso invalido no regreso el control")
		await _finish()
		return
	if InventorySystem.get_quantity("potion") != 1:
		push_error("battle_item_target_probe: un uso invalido consumio el objeto")
		await _finish()
		return
	if GameManager.party[0].hp_cur != lead_before:
		push_error("battle_item_target_probe: la criatura activa cambio con objeto invalido")
		await _finish()
		return
	if _manager.phase != _manager.Phase.PLAYER_TURN or not _manager._waiting_input:
		push_error("battle_item_target_probe: el uso invalido no regreso el turno al jugador")
		await _finish()
		return

	print("BATTLE_ITEM_TARGET_PROBE ok reserve_hp=%d potions=%d" % [
		GameManager.party[1].hp_cur,
		InventorySystem.get_quantity("potion"),
	])
	await _finish()

func _wait_until(predicate: Callable, timeout_seconds: float) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < int(timeout_seconds * 1000.0):
		if predicate.call():
			return true
		await get_tree().process_frame
	return false

func _finish() -> void:
	if _manager != null and is_instance_valid(_manager):
		_manager.queue_free()
		await get_tree().process_frame
		await get_tree().process_frame
	get_tree().quit()
