## SaveSystem.gd
## Autoload - Guardado persistente del progreso del jugador
## Usa FileAccess. Guarda: nivel actual, estadísticas, configuración.

extends Node

const SAVE_PATH := "user://savegame.dat"
const AUTO_SAVE_INTERVAL: float = 60.0  # segundos

var data: Dictionary = {
    "nivel_actual": "nivel_01",
    "vidas_totales_perdidas": 0,
    "monedas_totales": 0,
    "tiempo_total_segundos": 0.0,
    "mejor_tiempo_nivel": {},    # nivel_name -> float
    "configuracion": {
        "volumen_musica": 0.8,
        "volumen_sfx": 1.0,
        "bpm": 120.0,
    },
    "estadisticas": {
        "total_kills": 0,
        "total_checkpoints": 0,
        "niveles_completados": []
    }
}

var _autosave_timer: Timer = null

func _ready() -> void:
    load_game()
    _setup_autosave()
    _connect_signals()
    print("✅ SaveSystem inicializado")

func _setup_autosave() -> void:
    """Configura auto-guardado cada AUTO_SAVE_INTERVAL segundos"""
    _autosave_timer = Timer.new()
    _autosave_timer.wait_time = AUTO_SAVE_INTERVAL
    _autosave_timer.timeout.connect(save_game)
    add_child(_autosave_timer)
    _autosave_timer.start()

func _connect_signals() -> void:
    """Conecta eventos del juego para actualizar estadísticas"""
    if SignalBus.has_signal("player_died"):
        SignalBus.player_died.connect(_on_player_died)
    
    if SignalBus.has_signal("level_completed"):
        SignalBus.level_completed.connect(_on_level_completed)
    
    if SignalBus.has_signal("player_hit_checkpoint"):
        SignalBus.player_hit_checkpoint.connect(_on_checkpoint_hit)

## Guardar progreso en disco
func save_game() -> void:
    var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
    if f:
        f.store_var(data)
        print("💾 Progreso guardado")
    else:
        push_error("SaveSystem: No se pudo guardar en %s" % SAVE_PATH)

## Cargar progreso del disco
func load_game() -> void:
    if not FileAccess.file_exists(SAVE_PATH):
        print("📋 Primer inicio: sin datos previos")
        return
    
    var f := FileAccess.open(SAVE_PATH, FileAccess.READ)
    if f:
        var loaded = f.get_var()
        if loaded is Dictionary:
            data.merge(loaded, true)
            print("✅ Progreso cargado desde disco")
    else:
        push_error("SaveSystem: No se pudo cargar %s" % SAVE_PATH)

## Establecer valor en data
func set_value(key: String, value) -> void:
    data[key] = value
    save_game()

## Obtener valor de data
func get_value(key: String, default = null):
    return data.get(key, default)

## Borrar archivo de guardado (reset completo)
func delete_save() -> void:
    if FileAccess.file_exists(SAVE_PATH):
        DirAccess.remove_absolute(SAVE_PATH)
        print("🗑️ Guardado eliminado")
        data = {
            "nivel_actual": "nivel_01",
            "vidas_totales_perdidas": 0,
            "monedas_totales": 0,
            "tiempo_total_segundos": 0.0,
            "mejor_tiempo_nivel": {},
            "configuracion": {
                "volumen_musica": 0.8,
                "volumen_sfx": 1.0,
                "bpm": 120.0,
            },
            "estadisticas": {
                "total_kills": 0,
                "total_checkpoints": 0,
                "niveles_completados": []
            }
        }

## ===== CALLBACKS =====

func _on_player_died(player_id: int) -> void:
    data["vidas_totales_perdidas"] += 1
    # No auto-guardar en cada muerte (para no spamear)

func _on_level_completed(level_name: String, time_seconds: float) -> void:
    data["nivel_actual"] = level_name
    
    # Guardar mejor tiempo
    var mejor_tiempo = data["mejor_tiempo_nivel"].get(level_name, 999.0)
    if time_seconds < mejor_tiempo:
        data["mejor_tiempo_nivel"][level_name] = time_seconds
        print("🏃 Nuevo mejor tiempo en %s: %.2f segundos" % [level_name, time_seconds])
    
    # Registrar compleción
    if not data["estadisticas"]["niveles_completados"].has(level_name):
        data["estadisticas"]["niveles_completados"].append(level_name)
    
    save_game()

func _on_checkpoint_hit(player_id: int, checkpoint_id: String) -> void:
    data["estadisticas"]["total_checkpoints"] += 1

## Debug: mostrar todos los datos guardados
func print_save_data() -> void:
    print("=== DATOS GUARDADOS ===")
    print(data)
