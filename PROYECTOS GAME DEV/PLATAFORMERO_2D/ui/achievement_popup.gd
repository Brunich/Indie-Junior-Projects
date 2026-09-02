## achievement_popup.gd
## CanvasLayer con Panel animado. Se conecta a AchievementManager.achievement_unlocked.
## Muestra logros desbloqueados con cola automática

extends CanvasLayer

@onready var panel: Panel = $Panel
@onready var label_icono: Label = $Panel/HBox/LabelIcono
@onready var label_nombre: Label = $Panel/HBox/VBox/LabelNombre
@onready var label_categoria: Label = $Panel/HBox/VBox/LabelCategoria

const COLORES_CATEGORIA: Dictionary = {
    "historia": Color(0.3, 0.7, 1.0),      # Azul
    "habilidad": Color(1.0, 0.8, 0.2),    # Amarillo
    "secreto": Color(0.8, 0.3, 1.0),      # Púrpura
    "coop": Color(0.3, 1.0, 0.6),         # Verde
    "cosmetico": Color(1.0, 0.5, 0.3),    # Naranja
}

var _queue: Array = []
var _showing: bool = false

func _ready() -> void:
    panel.hide()
    panel.modulate.a = 0.0
    
    # Conectarse con AchievementManager
    var am = get_node_or_null("/root/AchievementManager")
    if am:
        am.achievement_unlocked.connect(_on_achievement_unlocked)
        print("✅ achievement_popup conectado con AchievementManager")
    else:
        push_warning("achievement_popup: AchievementManager no encontrado")

func _on_achievement_unlocked(id: String, data: Dictionary) -> void:
    """Llamado cuando se desbloquea un logro"""
    _queue.append(data)
    if not _showing:
        _show_next()

func _show_next() -> void:
    """Muestra el siguiente logro en la cola"""
    if _queue.is_empty():
        _showing = false
        return
    
    _showing = true
    var data: Dictionary = _queue.pop_front()
    
    # Actualizar UI
    label_icono.text = data.get("icono", "🏆")
    label_nombre.text = data.get("nombre", "Logro desbloqueado")
    label_categoria.text = data.get("categoria", "").capitalize()
    
    # Color según categoría
    var categoria = data.get("categoria", "")
    label_categoria.modulate = COLORES_CATEGORIA.get(categoria, Color.WHITE)
    
    # Reproducir SFX si existe
    var audio_manager = get_node_or_null("/root/AudioManager")
    if audio_manager:
        audio_manager.play_sfx("achievement_unlock")
    
    # Animación: slide desde derecha + fade in
    panel.modulate.a = 0.0
    panel.position.x = 400  # Fuera de pantalla (derecha)
    panel.show()
    
    var tween := create_tween()
    tween.set_parallel(true)
    tween.tween_property(panel, "modulate:a", 1.0, 0.3).set_ease(Tween.EASE_OUT)
    tween.tween_property(panel, "position:x", 0.0, 0.3).set_ease(Tween.EASE_OUT)
    
    # Mostrar durante 4 segundos
    await get_tree().create_timer(4.0).timeout
    
    # Animación: fade out + slide derecha
    var tween2 := create_tween()
    tween2.set_parallel(true)
    tween2.tween_property(panel, "modulate:a", 0.0, 0.3)
    tween2.tween_property(panel, "position:x", 400.0, 0.3)
    
    await tween2.finished
    panel.hide()
    
    # Mostrar siguiente
    _show_next()

## Estructura esperada de Scene (en editor):
## CanvasLayer
##   Panel (achievement_popup)
##     HBox
##       LabelIcono
##       VBox
##         LabelNombre
##         LabelCategoria
