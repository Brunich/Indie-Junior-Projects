## DialogueUI.gd — Panel que muestra diálogos en pantalla al estilo Hades 2
## Nodo: CanvasLayer > Panel > VBoxContainer > (Label nombre + RichTextLabel texto)
## Se conecta automáticamente al DialogueManager
extends CanvasLayer

@onready var panel: Panel = $Panel
@onready var label_nombre: Label = $Panel/VBox/LabelNombre
@onready var label_texto: RichTextLabel = $Panel/VBox/LabelTexto

## Diccionario de colores por personaje
const COLORES_PERSONAJE: Dictionary = {
    "thanatos": Color(0.6, 0.4, 1.0),   # morado burócrata
    "iris": Color(0.3, 0.9, 0.7),        # verde-cyan sarcástica
    "jugador": Color(1.0, 0.9, 0.3),     # amarillo del héroe
    "narrador": Color(0.8, 0.8, 0.8),    # gris narrador
}

func _ready() -> void:
    panel.hide()
    var dm := get_node_or_null("/root/DialogueManager")
    if dm:
        dm.dialogue_started.connect(_on_dialogue_started)
        dm.dialogue_ended.connect(_on_dialogue_ended)

func _on_dialogue_started(character: String, text: String) -> void:
    # Configurar nombre y color del personaje
    label_nombre.text = character.capitalize()
    label_nombre.modulate = COLORES_PERSONAJE.get(character.to_lower(), Color.WHITE)
    
    # Texto con typewriter effect
    label_texto.text = ""
    panel.show()
    _typewriter(text)

func _on_dialogue_ended() -> void:
    panel.hide()

func _typewriter(full_text: String) -> void:
    label_texto.text = ""
    for i in full_text.length():
        label_texto.text += full_text[i]
        await get_tree().create_timer(0.03).timeout
        # Saltar animación si el jugador presiona interactuar
        if Input.is_action_just_pressed("ui_accept"):
            label_texto.text = full_text
            return
