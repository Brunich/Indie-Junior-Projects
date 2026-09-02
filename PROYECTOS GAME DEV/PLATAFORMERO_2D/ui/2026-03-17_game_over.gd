## GameOver.gd — Pantalla de Game Over con stats y opciones
## Nodo: CanvasLayer > Control > VBox > (LabelTitulo, LabelStats, BtnReintentar, BtnMenu)
extends CanvasLayer

@onready var label_titulo: Label = $Control/VBox/LabelTitulo
@onready var label_stats: Label = $Control/VBox/LabelStats
@onready var btn_reintentar: Button = $Control/VBox/BtnReintentar
@onready var btn_menu: Button = $Control/VBox/BtnMenu

const ESCENA_MENU: String = "res://ui/menu_principal.tscn"

## Líneas de Thanatos al morir (se elige aleatoria)
const FRASES_THANATOS: Array[String] = [
    "Expediente cerrado. Sin apelación disponible.",
    "Causa de muerte: exceso de confianza. Clásico.",
    "Formulario de re-muerte. Ya viene prellenado.",
    "Error humano. Como siempre. Sin excepciones.",
    "Interesante estrategia. No funcionó. Anotado.",
]

func _ready() -> void:
    btn_reintentar.pressed.connect(_reintentar)
    btn_menu.pressed.connect(_volver_al_menu)
    
    # Frase aleatoria de Thanatos
    label_titulo.text = FRASES_THANATOS[randi() % FRASES_THANATOS.size()]
    
    # Conectar a GameManager para recibir stats
    var gm := get_node_or_null("/root/GameManager")
    if gm and gm.has_signal("game_over"):
        gm.game_over.connect(_mostrar_stats)

func _mostrar_stats(winner_id: int) -> void:
    var gm := get_node_or_null("/root/GameManager")
    if not gm:
        return
    var nm := get_node_or_null("/root/NetworkManager")
    var my_id: int = nm.get_unique_id() if nm else 1
    
    var score: int = gm.scores.get(my_id, 0)
    var lives_left: int = gm.lives.get(my_id, 0)
    label_stats.text = "Score: %d | Vidas restantes: %d" % [score, lives_left]

func _reintentar() -> void:
    get_tree().reload_current_scene()

func _volver_al_menu() -> void:
    get_tree().change_scene_to_file(ESCENA_MENU)
