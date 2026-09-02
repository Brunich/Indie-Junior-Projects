## menu_principal.gd — Menú principal del plataformero 2D
## Nodo raíz: Control (pantalla completa)
## Conecta con NetworkManager para modos local y multijugador.
## Usa get_node_or_null para evitar crashes si los autoloads no están presentes.
extends Control

# ── Constantes ────────────────────────────────────────────────────────────────
const NIVEL_INICIAL: String = "res://nivel_01.tscn"
const PUERTO: int = 7777

# ── Referencias a nodos ───────────────────────────────────────────────────────
@onready var btn_jugar: Button         = $VBox/BtnJugar
@onready var btn_multijugador: Button  = $VBox/BtnMultijugador
@onready var btn_salir: Button         = $VBox/BtnSalir
@onready var panel_multijugador: Control = $PanelMultijugador
@onready var input_ip: LineEdit        = $PanelMultijugador/VBoxMulti/InputIP
@onready var btn_host: Button          = $PanelMultijugador/VBoxMulti/BtnHost
@onready var btn_unirse: Button        = $PanelMultijugador/VBoxMulti/BtnUnirse

# ── Ciclo de vida ─────────────────────────────────────────────────────────────
func _ready() -> void:
	# Conectar botones del menú principal
	btn_jugar.pressed.connect(_jugar_local)
	btn_multijugador.pressed.connect(_toggle_panel_multi)
	btn_salir.pressed.connect(_salir)

	# Conectar botones del panel multijugador
	btn_host.pressed.connect(_iniciar_host)
	btn_unirse.pressed.connect(_unirse_a_partida)

	# Ocultar panel multijugador al iniciar
	if panel_multijugador:
		panel_multijugador.hide()

# ── Acciones del menú ─────────────────────────────────────────────────────────

## Inicia una partida local (un solo jugador).
func _jugar_local() -> void:
	var nm := get_node_or_null("/root/NetworkManager")
	if nm and nm.has_method("start_local"):
		nm.start_local(1)
	get_tree().change_scene_to_file(NIVEL_INICIAL)

## Muestra u oculta el panel de configuración multijugador.
func _toggle_panel_multi() -> void:
	if panel_multijugador:
		panel_multijugador.visible = not panel_multijugador.visible

## Cierra el juego.
func _salir() -> void:
	get_tree().quit()

# ── Acciones multijugador ─────────────────────────────────────────────────────

## Inicia el juego como host (servidor + cliente local).
func _iniciar_host() -> void:
	var nm := get_node_or_null("/root/NetworkManager")
	if nm and nm.has_method("host_game"):
		nm.host_game(PUERTO)
	else:
		push_warning("MenuPrincipal: NetworkManager no disponible, iniciando sin red")
	get_tree().change_scene_to_file(NIVEL_INICIAL)

## Se une a una partida existente usando la IP ingresada.
func _unirse_a_partida() -> void:
	var ip: String = input_ip.text.strip_edges()
	if ip.is_empty():
		ip = "127.0.0.1"
	var nm := get_node_or_null("/root/NetworkManager")
	if nm and nm.has_method("join_game"):
		nm.join_game(ip, PUERTO)
	else:
		push_warning("MenuPrincipal: NetworkManager no disponible, no se puede unir")
	get_tree().change_scene_to_file(NIVEL_INICIAL)
