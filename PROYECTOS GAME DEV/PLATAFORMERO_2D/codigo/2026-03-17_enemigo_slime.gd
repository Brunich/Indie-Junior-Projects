## ============================================================
## MECÁNICA: Enemigo Básico — Slime (IA de Patrulla)
## Generado: 17 de marzo 2026 | Semana 1 | Fase: Fundamentos
## Motor: Godot 4 / GDScript
## Para: Bruno — Indie Dev Portfolio | UANL Monterrey
## ============================================================
##
## QUÉ HACE ESTE CÓDIGO:
## Un slime que patrulla de izquierda a derecha.
## Al ver al jugador (dentro de su rango de detección), lo persigue.
## Si el jugador le dispara, pierde vida y muere con animación.
##
## CÓMO USARLO EN GODOT 4:
##   1. Nueva escena > CharacterBody2D (llámalo "Slime")
##   2. Hijos: CollisionShape2D + Sprite2D
##   3. Agrega al grupo "enemies" (Inspector > Groups > + enemies)
##   4. Adjunta este script
##   5. Asigna el sprite 2026-03-17_enemigo_slime.png
## ============================================================

extends CharacterBody2D

## ---- VARIABLES EXPORTABLES ----
@export var patrol_distance: float = 120.0    ## Distancia máxima de patrulla (px)
@export var patrol_speed: float = 60.0        ## Velocidad patrullando
@export var chase_speed: float = 100.0        ## Velocidad persiguiendo
@export var detection_range: float = 200.0    ## Rango para detectar al jugador
@export var max_health: int = 3               ## Vida máxima

## ---- VARIABLES DE ESTADO ----
var health: int                        ## Vida actual
var patrol_origin: Vector2             ## Punto de origen de la patrulla
var patrol_direction: float = 1.0     ## +1 derecha, -1 izquierda
var player_ref: Node2D = null          ## Referencia al jugador
var is_dead: bool = false              ## Para evitar procesar al morir

## ---- ESTADOS DE IA ----
enum State { PATROLLING, CHASING, HURT, DEAD }
var current_state: State = State.PATROLLING

## ---- REFERENCIA AL SPRITE ----
@onready var sprite: Sprite2D = $Sprite2D


func _ready() -> void:
	health = max_health
	patrol_origin = global_position  # Guardamos posición inicial

	# Buscar al jugador en el árbol de escenas
	# Asegúrate de que tu nodo jugador esté en el grupo "player"
	var players = get_tree().get_nodes_in_group("player")
	if players.size() > 0:
		player_ref = players[0]

	print("Slime listo con %d HP" % health)


func _physics_process(delta: float) -> void:
	if is_dead:
		return

	# Aplicar gravedad siempre
	var gravity_val = ProjectSettings.get_setting("physics/2d/default_gravity")
	if not is_on_floor():
		velocity.y += gravity_val * 2.0 * delta

	# Máquina de estados
	match current_state:
		State.PATROLLING:
			_do_patrol(delta)
		State.CHASING:
			_do_chase(delta)
		State.HURT:
			pass  # Inmovilizado durante el hurt

	move_and_slide()

	# Verificar si detecta al jugador → cambiar a CHASING
	_check_for_player()


## _do_patrol() — mueve el slime de un lado a otro
func _do_patrol(_delta: float) -> void:
	velocity.x = patrol_direction * patrol_speed
	sprite.flip_h = patrol_direction < 0.0

	# Si llegó al límite de su zona de patrulla, voltear
	var distance_from_origin = global_position.x - patrol_origin.x
	if abs(distance_from_origin) >= patrol_distance:
		patrol_direction *= -1.0

	# Si choca contra una pared, voltear
	if is_on_wall():
		patrol_direction *= -1.0


## _do_chase() — persigue al jugador
func _do_chase(_delta: float) -> void:
	if not player_ref or not is_instance_valid(player_ref):
		current_state = State.PATROLLING
		return

	var dist = player_ref.global_position.x - global_position.x
	var dir = sign(dist)
	velocity.x = dir * chase_speed
	sprite.flip_h = dir < 0.0

	# Si el jugador se fue muy lejos, volver a patrullar
	if abs(global_position.x - player_ref.global_position.x) > detection_range * 1.5:
		current_state = State.PATROLLING


## _check_for_player() — detecta si el jugador está cerca
func _check_for_player() -> void:
	if not player_ref or not is_instance_valid(player_ref):
		return

	var dist = global_position.distance_to(player_ref.global_position)
	if dist <= detection_range and current_state == State.PATROLLING:
		current_state = State.CHASING


## take_damage(amount) — llamado por balas u otras mecánicas
## Esta función es clave: las balas llaman body.take_damage(damage)
func take_damage(amount: int) -> void:
	if is_dead:
		return

	health -= amount
	print("Slime recibió %d daño. HP restante: %d" % [amount, health])

	if health <= 0:
		_die()
	else:
		_hurt_flash()


## _hurt_flash() — efecto visual de daño
func _hurt_flash() -> void:
	current_state = State.HURT
	# Flash rojo
	var tween = create_tween()
	tween.tween_property(sprite, "modulate", Color(1.5, 0.3, 0.3), 0.05)
	tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.1)
	tween.tween_callback(func(): current_state = State.CHASING if player_ref else State.PATROLLING)


## _die() — animación de muerte y destrucción
func _die() -> void:
	is_dead = true
	current_state = State.DEAD
	velocity = Vector2.ZERO

	print("¡Slime derrotado! +10 puntos")

	# Animación de desvanecimiento
	var tween = create_tween()
	tween.tween_property(self, "scale", Vector2(1.3, 0.3), 0.15)  # Aplastamiento
	tween.tween_property(self, "modulate:a", 0.0, 0.2)            # Desvanece
	tween.tween_callback(queue_free)                               # Destruir


# ============================================================
# CÓMO CONECTAR CON EL SISTEMA DE PUNTUACIÓN:
#
# En _die(), emite una señal:
#   signal enemy_killed(points)
#   emit_signal("enemy_killed", 10)
#
# Y en tu GameManager.gd:
#   slime.enemy_killed.connect(_on_enemy_killed)
#   func _on_enemy_killed(pts): score += pts
#
# VARIACIONES DE ENEMIGO (sin cambiar mucho este script):
# - Slime rápido: patrol_speed=100, chase_speed=180, max_health=1
# - Slime tanque: patrol_speed=30, max_health=8, detection_range=100
# - Slime saltarín: agrega salto en _do_chase cuando el jugador está sobre él
#
# PRÓXIMA MECÁNICA SUGERIDA: Sistema de puntuación + HUD
# ============================================================
