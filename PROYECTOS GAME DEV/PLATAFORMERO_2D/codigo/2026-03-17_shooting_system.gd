## ============================================================
## MECÁNICA: Sistema de Disparos (Plataformero 2D)
## Generado: 17 de marzo 2026 | Semana 1 | Fase: Fundamentos
## Motor: Godot 4 / GDScript
## Para: Bruno — Indie Dev Portfolio | UANL Monterrey
## ============================================================
##
## QUÉ HACE ESTE CÓDIGO:
## Permite al jugador disparar proyectiles en dirección horizontal.
## Genera balas como nodos instanciados (Bullet scene), las lanza
## con velocidad y las destruye al salir de pantalla o tocar algo.
##
## ESTE SCRIPT ES EN DOS PARTES:
##   1. bullet.gd     → va en la escena de la bala (Bullet.tscn)
##   2. player_shoot.gd → se agrega al CharacterBody2D del jugador
##
## CÓMO CONFIGURAR EN GODOT 4:
## PASO 1 — Crear la escena Bullet.tscn:
##   1. Archivo > Nueva Escena
##   2. Nodo raíz: Area2D (renómbralo "Bullet")
##   3. Hijos: CollisionShape2D + Sprite2D (o ColorRect para pruebas)
##   4. En CollisionShape2D: CapsuleShape2D rotado o CircleShape2D pequeño
##   5. Adjunta bullet.gd a "Bullet"
##   6. Guarda como res://scenes/Bullet.tscn
##
## PASO 2 — En tu CharacterBody2D (jugador):
##   1. Agrega player_shoot.gd (puedes combinar con player_movement.gd)
##   2. Asigna la variable `bullet_scene` en el Inspector
##   3. Agrega un Marker2D llamado "ShootPoint" como hijo del jugador
##      (posiciónalo en el centro-derecha del personaje)
##
## CONTROLES:
##   - Z o Ctrl izquierdo = Disparar
## ============================================================


# ==================================================================
# ARCHIVO 1: bullet.gd — Script para la bala
# Adjunta este código a tu nodo Area2D (Bullet.tscn)
# ==================================================================

# ---- INICIO bullet.gd ----
# extends Area2D
#
# @export var speed: float = 500.0        ## Velocidad de la bala (px/seg)
# @export var lifetime: float = 2.0       ## Tiempo máximo antes de destruirse
# @export var damage: int = 1             ## Daño que hace al enemigo
#
# var direction: float = 1.0             ## +1 = derecha, -1 = izquierda
# var _timer: float = 0.0
#
# func _ready() -> void:
#     # Cuando la bala toca algo, llamamos _on_hit()
#     body_entered.connect(_on_hit)
#
# func _physics_process(delta: float) -> void:
#     # Movemos la bala en la dirección asignada
#     position.x += speed * direction * delta
#     # Contamos el tiempo de vida
#     _timer += delta
#     if _timer >= lifetime:
#         queue_free()  # Destruir si lleva mucho tiempo
#
# func _on_hit(body: Node2D) -> void:
#     # Si golpea algo con grupo "enemy", le hace daño
#     if body.is_in_group("enemies"):
#         if body.has_method("take_damage"):
#             body.take_damage(damage)
#     queue_free()  # La bala se destruye al impactar
# ---- FIN bullet.gd ----


# ==================================================================
# ARCHIVO 2: player_shoot.gd
# Adjunta este script al CharacterBody2D del jugador
# (O agrégalo al final de player_movement.gd con extends CharacterBody2D)
# ==================================================================

extends CharacterBody2D

## ---- VARIABLES EXPORTABLES ----
@export var bullet_scene: PackedScene          ## Arrastra Bullet.tscn aquí
@export var shoot_cooldown: float = 0.25       ## Segundos entre disparos
@export var max_bullets_on_screen: int = 5     ## Límite de balas simultáneas

## ---- REFERENCIA A NODOS ----
## Asegúrate de tener un Marker2D llamado "ShootPoint" como hijo del jugador
@onready var shoot_point: Marker2D = $ShootPoint

## ---- VARIABLES INTERNAS ----
var _cooldown_timer: float = 0.0   ## Contador del cooldown entre disparos
var _facing_right: bool = true     ## Dirección donde mira el jugador
var _bullet_count: int = 0         ## Contador de balas en pantalla


## _ready() — configuración inicial
func _ready() -> void:
	print("Sistema de disparos activo. Presiona Z para disparar.")
	# Verificamos que la escena de bala esté asignada
	if not bullet_scene:
		push_warning("⚠️ bullet_scene no está asignado en el Inspector!")


## _physics_process(delta) — se llama 60 veces por segundo
func _physics_process(delta: float) -> void:

	# ---- MOVIMIENTO (mismo que player_movement.gd) ----
	# Si ya tienes player_movement.gd, puedes borrar esta sección
	# y solo dejar la parte de DISPAROS
	_handle_movement(delta)

	# ---- COOLDOWN DE DISPARO ----
	if _cooldown_timer > 0.0:
		_cooldown_timer -= delta

	# ---- DETECTAR INPUT DE DISPARO ----
	# "shoot" = acción personalizada, ve a Project > Input Map > Agrega "shoot"
	# y asígnale la tecla Z o Ctrl izquierdo
	if Input.is_action_just_pressed("shoot") or Input.is_action_just_pressed("ui_select"):
		_try_shoot()

	move_and_slide()


## _handle_movement(delta) — movimiento básico del jugador
## (Integrado aquí para que sea un script completo)
func _handle_movement(delta: float) -> void:
	var gravity_val: float = ProjectSettings.get_setting("physics/2d/default_gravity")

	# Gravedad
	if not is_on_floor():
		velocity.y += gravity_val * 2.5 * delta

	# Salto
	if Input.is_action_just_pressed("ui_accept") and is_on_floor():
		velocity.y = -450.0

	# Movimiento horizontal
	var direction: float = Input.get_axis("ui_left", "ui_right")
	if direction != 0.0:
		velocity.x = direction * 200.0
		_facing_right = direction > 0.0  # Actualizamos la dirección
	else:
		velocity.x = move_toward(velocity.x, 0.0, 40.0)


## _try_shoot() — intenta crear una bala si se cumplen las condiciones
func _try_shoot() -> void:
	# Verificar cooldown
	if _cooldown_timer > 0.0:
		return

	# Verificar límite de balas en pantalla
	if _bullet_count >= max_bullets_on_screen:
		return

	# Verificar que la escena de bala exista
	if not bullet_scene:
		push_warning("⚠️ No hay bullet_scene asignado!")
		return

	# ---- CREAR LA BALA ----
	var bullet = bullet_scene.instantiate()

	# Posición de spawn: desde el ShootPoint (o desde el jugador si no existe)
	if shoot_point:
		bullet.global_position = shoot_point.global_position
	else:
		bullet.global_position = global_position

	# Asignar dirección de la bala según hacia dónde mira el jugador
	bullet.direction = 1.0 if _facing_right else -1.0

	# Conectar señal para saber cuándo se destruye (para contar balas)
	bullet.tree_exited.connect(_on_bullet_destroyed)

	# Agregar la bala al mismo nivel que el jugador (no como hijo)
	# Esto evita que la bala se mueva junto con el jugador
	get_parent().add_child(bullet)

	# Actualizar contadores
	_bullet_count += 1
	_cooldown_timer = shoot_cooldown

	# Efecto visual opcional: "empujar" levemente al jugador hacia atrás
	# velocity.x -= bullet.direction * 30.0  # Descomenta para efecto de retroceso


## _on_bullet_destroyed() — se llama cuando una bala sale de pantalla o impacta
func _on_bullet_destroyed() -> void:
	_bullet_count = max(0, _bullet_count - 1)


# ============================================================
# PARA PROBAR SIN LA ESCENA Bullet.tscn (prueba rápida):
#
# 1. En _try_shoot(), reemplaza bullet_scene.instantiate() con:
#    var bullet = ColorRect.new()
#    bullet.size = Vector2(12, 6)
#    bullet.color = Color(1, 0.8, 0.2)  # Color dorado
#    bullet.set_script(bullet_gd_resource)
#
# 2. O simplemente usa un Area2D con script inline.
#
# PRÓXIMOS PASOS SUGERIDOS:
# 1. Agrega animación de disparo al sprite del jugador
# 2. Crea un enemigo con script que responda a take_damage()
# 3. Agrega efecto de partículas al impacto (GPUParticles2D)
# 4. Agrega sonido de disparo (AudioStreamPlayer2D)
#
# MECÁNICA SIGUIENTE SUGERIDA: Enemigo básico con IA (patrulla + persecución)
# ============================================================
