## AchievementManager.gd
## Autoload — Gestiona logros, persistencia y recompensas
## Se conecta con achievements_db.gd para los datos

extends Node

signal achievement_unlocked(id: String, data: Dictionary)
signal stat_updated(key: String, value: int)

const SAVE_PATH := "user://achievements.dat"

var _unlocked: Dictionary = {}    # id -> {"timestamp": int, "equipped": bool}
var _stats: Dictionary = {}       # "deaths_nivel_01" -> 3, etc.
var _db: Dictionary = {}          # cargado desde achievements_db.gd

func _ready() -> void:
    # Cargar DB desde achievements_db.gd
    var db_script = load("res://codigo/achievements_db.gd")
    if db_script:
        var db_instance = db_script.new()
        _db = db_instance.DATA
        db_instance.queue_free()
    else:
        push_error("AchievementManager: No se pudo cargar achievements_db.gd")
        return
    
    _load_save()
    
    # Conectar con SignalBus si existe
    if SignalBus.has_signal("enemy_died"):
        SignalBus.enemy_died.connect(_on_enemy_died)
    if SignalBus.has_signal("player_died"):
        SignalBus.player_died.connect(_on_player_died)
    if SignalBus.has_signal("level_completed"):
        SignalBus.level_completed.connect(_on_level_completed)

## Incrementar un contador y revisar si desbloquea algún logro
func increment_stat(key: String, amount: int = 1) -> void:
    _stats[key] = _stats.get(key, 0) + amount
    stat_updated.emit(key, _stats[key])
    _check_triggers_for_stat(key)
    _save()

## Desbloquear directamente por ID
func unlock(id: String) -> void:
    if _unlocked.has(id):
        return  # ya desbloqueado
    if not _db.has(id):
        push_warning("AchievementManager: logro '%s' no existe en DB" % id)
        return
    
    _unlocked[id] = {
        "timestamp": Time.get_unix_time_from_system(),
        "equipped": false
    }
    
    achievement_unlocked.emit(id, _db[id])
    _save()
    print("🏆 LOGRO DESBLOQUEADO: %s" % _db[id].get("nombre", id))

func is_unlocked(id: String) -> bool:
    return _unlocked.has(id)

func get_stat(key: String) -> int:
    return _stats.get(key, 0)

func get_unlocked_ids() -> Array:
    return _unlocked.keys()

func get_unlocked_count() -> int:
    return _unlocked.size()

func get_total_count() -> int:
    return _db.size()

func get_achievement_data(id: String) -> Dictionary:
    return _db.get(id, {})

func get_all_achievements() -> Dictionary:
    return _db

## Retorna solo los logros no secretos o desbloqueados
func get_visible_achievements() -> Array:
    var visible = []
    for id in _db.keys():
        var achievement = _db[id]
        if not achievement.get("secreto", false) or _unlocked.has(id):
            visible.append({"id": id, "data": achievement})
    return visible

## Obtener recompensas equipadas
func get_equipped_rewards() -> Array:
    var rewards := []
    for id in _unlocked:
        if _unlocked[id].get("equipped", false):
            var reward = _db[id].get("recompensa", {})
            if reward and reward.get("tipo") != "none":
                rewards.append(reward)
    return rewards

## Equipar una recompensa
func equip_reward(id: String) -> void:
    if _unlocked.has(id):
        _unlocked[id]["equipped"] = true
        _save()

## Desequipar una recompensa
func unequip_reward(id: String) -> void:
    if _unlocked.has(id):
        _unlocked[id]["equipped"] = false
        _save()

## ===== TRIGGERS INTERNOS =====

func _check_triggers_for_stat(key: String) -> void:
    for id in _db:
        if _unlocked.has(id):
            continue
        
        var trigger = _db[id].get("trigger", {})
        if trigger.get("tipo") != "contador":
            continue
        
        if trigger.get("evento") != key:
            continue
        
        var required = trigger.get("valor", 1)
        var exacto = trigger.get("exacto", false)
        var current = _stats.get(key, 0)
        
        if exacto and current == required:
            unlock(id)
        elif not exacto and current >= required:
            unlock(id)

func _on_player_died(player_id: int) -> void:
    increment_stat("total_deaths")
    increment_stat("deaths_in_level")
    
    # Buscar nivel actual y incrementar estadística específica
    var current_level = _get_current_level()
    if current_level:
        increment_stat("deaths_%s" % current_level)

func _on_enemy_died(enemy_id: int, position: Vector2) -> void:
    increment_stat("total_kills")
    increment_stat("kills_in_level")

func _on_level_completed(level_name: String, time_seconds: float) -> void:
    # Desbloquear logros de compleción de nivel
    for id in _db:
        if _unlocked.has(id):
            continue
        
        var trigger = _db[id].get("trigger", {})
        if trigger.get("tipo") == "evento" and trigger.get("evento") == "level_completed":
            if trigger.get("nivel") == level_name:
                unlock(id)
    
    # Verificar logros de tiempo
    for id in _db:
        if _unlocked.has(id):
            continue
        
        var trigger = _db[id].get("trigger", {})
        if trigger.get("tipo") == "tiempo" and trigger.get("evento") == "level_completed":
            if trigger.get("nivel") == level_name:
                var required_time = trigger.get("valor", 999)
                if time_seconds < required_time:
                    unlock(id)

func _get_current_level() -> String:
    var scene = get_tree().current_scene
    if scene:
        return scene.name.to_lower()
    return ""

## ===== PERSISTENCIA =====

func _save() -> void:
    var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
    if f:
        f.store_var({"unlocked": _unlocked, "stats": _stats})
        print("💾 Logros guardados")

func _load_save() -> void:
    if not FileAccess.file_exists(SAVE_PATH):
        print("📋 Primer inicio: sin logros previos")
        return
    
    var f := FileAccess.open(SAVE_PATH, FileAccess.READ)
    if f:
        var data = f.get_var()
        if data is Dictionary:
            _unlocked = data.get("unlocked", {})
            _stats = data.get("stats", {})
            print("✅ Logros cargados: %d desbloqueados" % _unlocked.size())

## Debug: mostrar todos los stats
func print_stats() -> void:
    print("=== ESTADÍSTICAS ===")
    for key in _stats.keys():
        print("%s: %d" % [key, _stats[key]])

## Debug: mostrar todos los logros desbloqueados
func print_unlocked() -> void:
    print("=== LOGROS DESBLOQUEADOS (%d/%d) ===" % [_unlocked.size(), _db.size()])
    for id in _unlocked.keys():
        var data = _db[id]
        print("✓ %s (%s) — %d pts" % [data.get("nombre", id), data.get("categoria", "?"), data.get("puntos", 0)])

## Debug: desbloquear logro manualmente (solo en editor)
func debug_unlock(id: String) -> void:
    if not OS.is_debug_build():
        return
    unlock(id)
