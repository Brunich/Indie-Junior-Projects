## MenuPrincipal.gd — Menú de inicio del juego
## Nodo: Control > VBoxContainer > (LabelTitulo, BtnJugar, BtnMultijugador, BtnSalir)
extends Control

@onready var btn_jugar: Button = $VBox/BtnJugar
@onready var btn_multijugador: Button = $VBox/BtnMultijugador
@onready var btn_salir: Button = $VBox/BtnSalir
@onready var panel_multijugador: Control = $PanelMultijugador
@onready var input_ip: LineEdit = $PanelMultijugador/InputIP
@onready var btn_host: Button = $PanelMultijugador/BtnHost
@onready var btn_unirse: Button = $PanelMultijugador/BtnUnirse

const NIVEL_INICIAL: String = "res://nivel_01.tscn"
const PUERTO: int = 7777

func _ready() -> void:
    btn_jugar.pressed.connect(_jugar_local)
    btn_multijugador.pressed.connect(_toggle_panel_multi)
    btn_salir.pressed.connect(get_tree().quit)
    btn_host.pressed.connect(_iniciar_host)
    btn_unirse.pressed.connect(_unirse_a_partida)
    
    if panel_multijugador:
        panel_multijugador.hide()

func _jugar_local() -> void:
    var nm := get_node_or_null("/root/NetworkManager")
    if nm:
        nm.start_local(1)
    get_tree().change_scene_to_file(NIVEL_INICIAL)

func _toggle_panel_multi() -> void:
    if panel_multijugador:
        panel_multijugador.visible = not panel_multijugador.visible

func _iniciar_host() -> void:
    var nm := get_node_or_null("/root/NetworkManager")
    if nm:
        nm.host_game(PUERTO)
    get_tree().change_scene_to_file(NIVEL_INICIAL)

func _unirse_a_partida() -> void:
    var ip: String = input_ip.text.strip_edges()
    if ip.is_empty():
        ip = "127.0.0.1"
    var nm := get_node_or_null("/root/NetworkManager")
    if nm:
        nm.join_game(ip, PUERTO)
    get_tree().change_scene_to_file(NIVEL_INICIAL)
