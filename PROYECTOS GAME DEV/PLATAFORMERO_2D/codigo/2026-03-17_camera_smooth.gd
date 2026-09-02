## ============================================================
## camera_smooth.gd — Cámara suave que sigue al jugador
## Bruno Salas | UANL Monterrey | 2026
## ============================================================
## Sigue al player con suavidad, mantiene distancia de bordes
## Multiplayer: cámara enfocada en el player local

extends Camera2D
class_name CameraController

# ---- PROPIEDADES ----
@export var follow_speed: float = 5.0              ## Qué tan rápido sigue (0 = instant)
@export var camera_distance: Vector2 = Vector2.ZERO  ## Offset del player
@export var zoom_level: float = 1.5                ## Zoom inicial
@export var min_zoom: float = 1.0
@export var max_zoom: float = 3.0
@export var lookahead_distance: float = 50.0       ## Distancia en dirección del movimiento

# ---- REFERENCIAS ----
@onready var viewport_rect = get_viewport_rect()

var _target: Node2D = null
var _current_pos: Vector2 = Vector2.ZERO
var _target_pos: Vector2 = Vector2.ZERO

func _ready() -> void:
	# Buscar el player en el árbol
	var players = get_tree().get_nodes_in_group("player")
	for p in players:
		# En multiplayer, seguir solo el player local
		if p.is_multiplayer_authority() or not multiplayer.has_multiplayer_peer():
			_target = p
			break

	if _target:
		global_position = _target.global_position
		_current_pos = global_position
		zoom = Vector2(zoom_level, zoom_level)
	else:
		push_warning("CameraController: No se encontró ningún player en el grupo 'player'")

func _process(delta: float) -> void:
	if not _target:
		return

	_update_target_position()
	_smooth_follow(delta)
	_apply_lookahead()

func _update_target_position() -> void:
	## Calcula la posición objetivo basada en el player
	_target_pos = _target.global_position + camera_distance

	# Obtener el tamaño visible de la pantalla
	var viewport_size = get_viewport_rect().size / zoom

	# Limitar la cámara para no salir de los bordes del nivel
	# (asumir que el nivel tiene límites conocidos)
	_target_pos.x = clamp(_target_pos.x, viewport_size.x * 0.5, 1920 - viewport_size.x * 0.5)
	_target_pos.y = clamp(_target_pos.y, viewport_size.y * 0.5, 1080 - viewport_size.y * 0.5)

func _smooth_follow(delta: float) -> void:
	## Interpola suavemente a la posición objetivo
	if follow_speed > 0.0:
		_current_pos = _current_pos.lerp(_target_pos, follow_speed * delta)
	else:
		_current_pos = _target_pos

	global_position = _current_pos.round()  # Round para evitar blur en pixel art

func _apply_lookahead() -> void:
	## Desplaza la cámara ligeramente hacia donde se mueve el player
	if _target.velocity.length() > 10.0:
		var direction = _target.velocity.normalized()
		var lookahead = direction * lookahead_distance
		global_position += lookahead * 0.1

func set_zoom_level(level: float) -> void:
	## Cambia el zoom suavemente
	level = clamp(level, min_zoom, max_zoom)

	var tween = create_tween()
	tween.set_trans(Tween.TRANS_SINE)
	tween.tween_property(self, "zoom", Vector2(level, level), 0.5)
	zoom_level = level

func set_follow_target(target: Node2D) -> void:
	## Cambia el target seguido por la cámara
	_target = target
	if _target:
		_target_pos = _target.global_position

func shake(intensity: float = 0.2, duration: float = 0.15) -> void:
	## Efecto de temblor al recibir impacto
	var original_pos = global_position
	var tween = create_tween()

	for i in range(int(duration * 60)):  # 60 FPS
		var offset = Vector2(
			randf_range(-intensity, intensity),
			randf_range(-intensity, intensity)
		)
		tween.tween_callback(func(): global_position = original_pos + offset)
		tween.tween_callback(func(): await get_tree().process_frame)

	tween.tween_callback(func(): global_position = original_pos)
