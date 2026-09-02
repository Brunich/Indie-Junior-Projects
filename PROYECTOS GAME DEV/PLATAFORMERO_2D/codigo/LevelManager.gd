## LevelManager.gd
## Autoload - Gestiona transiciones entre niveles con screen_transition.gdshader

extends Node

signal transition_finished
signal level_loaded(level_name: String)

const TRANSITION_DURATION: float = 0.5
const SHADER_PATH: String = "res://shaders/screen_transition.gdshader"

var _transitioning: bool = false
var _current_level: String = ""

func _ready() -> void:
    _current_level = get_tree().current_scene.name
    print("✅ LevelManager inicializado en '%s'" % _current_level)

## Cambiar de nivel con transición circular/shader
func go_to_level(scene_path: String) -> void:
    if _transitioning:
        push_warning("LevelManager: Transición ya en progreso")
        return
    
    _transitioning = true
    print("🔄 Transición a: %s" % scene_path)
    
    # Notificar inicio de transición
    SignalBus.level_transition_requested.emit(scene_path)
    
    # Buscar CanvasLayer de transición en la escena actual
    var transition = get_tree().get_first_node_in_group("screen_transition")
    
    if transition:
        var tween := create_tween()
        tween.tween_property(transition, "material:shader_parameter/progress", 1.0, TRANSITION_DURATION).set_ease(Tween.EASE_IN)
        await tween.finished
    
    # Cambiar escena
    await get_tree().change_scene_to_file(scene_path)
    
    # Fade in en la nueva escena
    var new_transition = get_tree().get_first_node_in_group("screen_transition")
    if new_transition:
        new_transition.material.set_shader_parameter("progress", 1.0)
        var tween2 := create_tween()
        tween2.tween_property(new_transition, "material:shader_parameter/progress", 0.0, TRANSITION_DURATION).set_ease(Tween.EASE_OUT)
        await tween2.finished
    
    _current_level = get_tree().current_scene.name
    _transitioning = false
    transition_finished.emit()
    
    SignalBus.level_started.emit(_current_level)
    level_loaded.emit(_current_level)
    print("✅ Nivel cargado: %s" % _current_level)

## Recargar nivel actual
func restart_level() -> void:
    var current_scene = get_tree().current_scene.scene_file_path
    await go_to_level(current_scene)

## Retornar al menú principal
func go_to_menu() -> void:
    await go_to_level("res://escenas/menu_principal.tscn")

## Obtener nivel actual
func get_current_level() -> String:
    return _current_level

## Esperar a que termine la transición
func wait_for_transition() -> void:
    await transition_finished
