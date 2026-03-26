extends Node

const BattleManager := preload("res://codigo/batalla/battle_manager.gd")
const CreatureInstance := preload("res://codigo/recursos/creature_instance.gd")
const MoveData := preload("res://codigo/recursos/move_data.gd")

func _ready() -> void:
	call_deferred("_run")

func _run() -> void:
	var manager := BattleManager.new()
	add_child(manager)

	var scarf_user := CreatureInstance.create("coylto", 20)
	var base_speed := manager._battle_speed(scarf_user)
	scarf_user.held_item = "Choice Scarf"
	var scarf_speed := manager._battle_speed(scarf_user)
	if scarf_speed <= base_speed:
		push_error("held_item_probe: Choice Scarf no subio velocidad")
		get_tree().quit()
		return

	var attacker := CreatureInstance.create("embralcinder", 24)
	var target := CreatureInstance.create("larvox", 24)
	var no_item_damage := manager._calc_damage(attacker, target, MoveData.slash())
	target.held_item = "Eviolite"
	var eviolite_damage := manager._calc_damage(attacker, target, MoveData.slash())
	if eviolite_damage >= no_item_damage:
		push_error("held_item_probe: Eviolite no redujo dano")
		get_tree().quit()
		return

	var balloon_target := CreatureInstance.create("larvox", 20)
	balloon_target.held_item = "Air Balloon"
	var balloon_eff := manager._type_effectiveness(MoveData.earthquake(), balloon_target)
	if balloon_eff != 0.0:
		push_error("held_item_probe: Air Balloon no dio inmunidad a Ground")
		get_tree().quit()
		return

	var lum_target := CreatureInstance.create("folimp", 18)
	lum_target.held_item = "Lum Berry"
	lum_target.status = CreatureInstance.Status.BURNED
	var lum_msg := lum_target.check_status_cure_item()
	if lum_msg == "" or lum_target.status != CreatureInstance.Status.NONE:
		push_error("held_item_probe: Lum Berry no curo estado")
		get_tree().quit()
		return

	var sash_target := CreatureInstance.create("folimp", 18)
	sash_target.held_item = "Focus Sash"
	var gate_result: Dictionary = manager._apply_damage_gate_item(sash_target, MoveData.slash(), sash_target.hp_cur + 50)
	if int(gate_result.get("damage", 0)) != sash_target.hp_cur - 1:
		push_error("held_item_probe: Focus Sash no dejo a 1 HP")
		get_tree().quit()
		return

	print("HELD_ITEM_PROBE ok speed=%d eviolite=%d/%d" % [scarf_speed, eviolite_damage, no_item_damage])
	get_tree().quit()
