extends SceneTree

const CreatureInstance := preload("res://codigo/recursos/creature_instance.gd")
const PokedexData := preload("res://codigo/recursos/pokedex_data.gd")
const RuntimeTextureLoader := preload("res://codigo/util/runtime_texture_loader.gd")

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var generated_count := 0
	for entry in PokedexData.get_catalogue():
		if int(entry.get("number", 0)) < 34:
			continue
		generated_count += 1
		var creature_id := String(entry.get("id", ""))
		var creature := CreatureInstance.create(creature_id, 16)
		if creature.display_name().strip_edges() == "":
			push_error("exec_final_creature_integration_probe: nombre vacio en %s" % creature_id)
			quit(1)
			return
		if creature.type1.strip_edges() == "":
			push_error("exec_final_creature_integration_probe: tipo principal vacio en %s" % creature_id)
			quit(1)
			return
		if creature.hp_max <= 0 or creature.atk <= 0 or creature.def <= 0 or creature.sp_atk <= 0 or creature.sp_def <= 0 or creature.speed <= 0:
			push_error("exec_final_creature_integration_probe: stats invalidos en %s" % creature_id)
			quit(1)
			return
		if creature.moves.is_empty():
			push_error("exec_final_creature_integration_probe: sin moveset en %s" % creature_id)
			quit(1)
			return
		var sprite_path := "res://sprites/pokemon/emberveil/%s_base.png" % creature_id
		if RuntimeTextureLoader.load_texture(sprite_path) == null:
			push_error("exec_final_creature_integration_probe: falta sprite %s" % sprite_path)
			quit(1)
			return

	print("FINAL_CREATURE_INTEGRATION_PROBE ok count=%d" % generated_count)
	quit()
