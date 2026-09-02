## ============================================================
## player_state_machine.gd — Plataformero 2D | Nivel Avanzado
## Bruno Salas | UANL Monterrey | 2026
## ============================================================
## ARQUITECTURA: Finite State Machine (FSM) con enum
##
## Por qué FSM y no un montón de if/else:
##   - Cada estado tiene su propia lógica de entrada, proceso y salida
##   - Es imposible que dos estados se "pisen" entre sí
##   - Añadir un estado nuevo (ej: dash, wall-slide) no rompe los demás
##   - Es la arquitectura que usan juegos como Hollow Knight, Celeste
##
## ESTADOS DEL JUGADOR:
##   IDLE → RUNNING → JUMPING → FALLING → LANDING → HURT → DEAD
##   (con transiciones explícitas entre cada par de estados)
## ============================================================

class_name PlayerController
extends CharacterBody2D

# ---- ESTADOS ----
enum State {
	IDLE,       # Parado, en el suelo
	RUNNING,    # Corriendo, en el suelo
	JUMPING,    # Subiendo (velocity.y < 0)
	FALLING,    # Bajando (velocity.y > 0)
	LANDING,    # Frame de aterrizaje (pequeña pausa visual)
	WALL_SLIDE, # Deslizándose por una pared
	HURT,       # Recibió daño (inmovilizado brevemente)
	DEAD        # Muerto
}

# ---- PARÁMETROS EXPORTABLES (editables en Inspector) ----
@export_group("Movimiento")
@export var run_speed: float        = 220.0   ## Velocidad horizontal (px/s)
@export var acceleration: float     = 1800.0  ## Qué tan rápido alcanza run_speed
@export var deceleration: float     = 1400.0  ## Frenado al soltar dirección
@export var air_control: float      = 0.6     ## Multiplicador de control en el aire (0-1)

@export_group("Salto")
@export var jump_force: float       = -520.0  ## Impulso inicial del salto
@export var jump_cut: float         = 0.45    ## Multiplica velocity.y al soltar el botón (salto corto)
@export var gravity_up: float       = 1800.0  ## Gravedad mientras sube (más lenta = más flotante)
@export var gravity_down: float     = 2800.0  ## Gravedad mientras baja (más pesada = más responsivo)
@export var max_fall_speed: float   = 600.0   ## Límite de velocidad de caída
@export var coyote_time: float      = 0.10    ## Segundos después del borde donde aún se puede saltar
@export var jump_buffer: float      = 0.12    ## Segundos antes de tocar suelo donde se guarda el salto

@export_group("Wall Slide")
@export var wall_slide_speed: float = 60.0    ## Velocidad de deslizamiento por pared
@export var wall_jump_x: float      = 280.0   ## Impulso horizontal en wall jump
@export var wall_jump_y: float      = -480.0  ## Impulso vertical en wall jump

@export_group("Vida")
@export var max_health: int         = 5
@export var hurt_duration: float    = 0.4     ## Segundos de inmovilidad al recibir daño
@export var hurt_knockback: float   = 300.0   ## Fuerza de retroceso al recibir daño
@export var invincibility_time: float = 0.8   ## Segundos de invencibilidad tras daño

# ---- SEÑALES ----
signal state_changed(old_state: State, new_state: State)
signal health_changed(current: int, maximum: int)
signal died()
signal landed()
signal jumped()

# ---- REFERENCIAS A NODOS ----
@onready var sprite: AnimatedSprite2D  = $AnimatedSprite2D
@onready var hitbox: CollisionShape2D  = $CollisionShape2D
@onready var wall_checker_l: RayCast2D = $WallCheckerLeft
@onready var wall_checker_r: RayCast2D = $WallCheckerRight
@onready var coyote_timer: Timer       = $CoyoteTimer
@onready var hurt_timer: Timer         = $HurtTimer
@onready var inv_timer: Timer          = $InvincibilityTimer

# ---- VARIABLES INTERNAS ----
var current_state: State = State.IDLE
var health: int
var jump_buffer_timer: float = 0.0
var facing_right: bool = true
var was_on_floor: bool = false
var is_invincible: bool = false


# ==================================================================
# _ready — configuración inicial
# ==================================================================
func _ready() -> void:
	health = max_health
	_setup_timers()
	_enter_state(State.IDLE)
	add_to_group("player")


func _setup_timers() -> void:
	# Si no tienes los nodos Timer en la escena, se crean en código
	if not has_node("CoyoteTimer"):
		var t = Timer.new(); t.name = "CoyoteTimer"; t.one_shot = true; add_child(t)
	if not has_node("HurtTimer"):
		var t = Timer.new(); t.name = "HurtTimer"; t.one_shot = true; add_child(t)
	if not has_node("InvincibilityTimer"):
		var t = Timer.new(); t.name = "InvincibilityTimer"; t.one_shot = true; add_child(t)


# ==================================================================
# _physics_process — tick principal (60fps)
# ==================================================================
func _physics_process(delta: float) -> void:
	if current_state == State.DEAD:
		return

	_update_timers(delta)
	_update_gravity(delta)
	_process_state(delta)

	was_on_floor = is_on_floor()
	move_and_slide()
	_check_state_transitions()


# ==================================================================
# TIMERS
# ==================================================================
func _update_timers(delta: float) -> void:
	if jump_buffer_timer > 0.0:
		jump_buffer_timer -= delta

	# Coyote time: si acaba de salir del borde, inicia el timer
	if was_on_floor and not is_on_floor():
		if current_state != State.JUMPING:
			coyote_timer.start(coyote_time)


# ==================================================================
# GRAVEDAD — diferente arriba vs abajo (feel más responsivo)
# ==================================================================
func _update_gravity(delta: float) -> void:
	if is_on_floor():
		velocity.y = 0.0
		return

	var grav = gravity_up if velocity.y < 0.0 else gravity_down
	velocity.y = min(velocity.y + grav * delta, max_fall_speed)


# ==================================================================
# MÁQUINA DE ESTADOS — cada estado procesa su propia lógica
# ==================================================================
func _process_state(delta: float) -> void:
	match current_state:
		State.IDLE:      _state_idle(delta)
		State.RUNNING:   _state_running(delta)
		State.JUMPING:   _state_jumping(delta)
		State.FALLING:   _state_falling(delta)
		State.LANDING:   _state_landing(delta)
		State.WALL_SLIDE:_state_wall_slide(delta)
		State.HURT:      _state_hurt(delta)


func _state_idle(delta: float) -> void:
	_apply_horizontal(0.0, delta)
	_check_jump_input()
	if Input.get_axis("ui_left", "ui_right") != 0.0:
		_enter_state(State.RUNNING)


func _state_running(delta: float) -> void:
	var dir = Input.get_axis("ui_left", "ui_right")
	_apply_horizontal(dir, delta)
	_check_jump_input()
	_update_facing(dir)
	if dir == 0.0:
		_enter_state(State.IDLE)


func _state_jumping(delta: float) -> void:
	var dir = Input.get_axis("ui_left", "ui_right")
	_apply_horizontal(dir, delta * air_control)
	_update_facing(dir)

	# Salto corto: soltar el botón reduce la velocidad vertical
	if Input.is_action_just_released("jump") and velocity.y < 0.0:
		velocity.y *= jump_cut

	if velocity.y >= 0.0:
		_enter_state(State.FALLING)


func _state_falling(delta: float) -> void:
	var dir = Input.get_axis("ui_left", "ui_right")
	_apply_horizontal(dir, delta * air_control)
	_update_facing(dir)
	_check_jump_input()

	# Wall slide
	if _is_touching_wall() and dir != 0.0:
		_enter_state(State.WALL_SLIDE)


func _state_landing(_delta: float) -> void:
	# Frame de aterrizaje — breve pausa visual
	_apply_horizontal(0.0, _delta)
	if sprite.frame >= sprite.sprite_frames.get_frame_count("landing") - 1:
		_enter_state(State.IDLE)


func _state_wall_slide(delta: float) -> void:
	# Frenar la caída
	velocity.y = move_toward(velocity.y, wall_slide_speed, gravity_down * delta)

	# Wall jump
	if Input.is_action_just_pressed("jump"):
		var wall_dir = -1.0 if wall_checker_r.is_colliding() else 1.0
		velocity.x = wall_dir * wall_jump_x
		velocity.y = wall_jump_y
		_enter_state(State.JUMPING)
		emit_signal("jumped")
		return

	# Salir de wall slide si suelta la dirección o toca suelo
	if not _is_touching_wall() or is_on_floor():
		_enter_state(State.IDLE if is_on_floor() else State.FALLING)


func _state_hurt(_delta: float) -> void:
	# Inmovilizado — esperar que el timer termine
	velocity.x = move_toward(velocity.x, 0.0, 800.0 * _delta)
	if hurt_timer.is_stopped():
		_enter_state(State.IDLE if is_on_floor() else State.FALLING)


# ==================================================================
# TRANSICIONES — chequeos automáticos cada frame
# ==================================================================
func _check_state_transitions() -> void:
	# Aterrizaje
	if not was_on_floor and is_on_floor():
		if current_state == State.FALLING:
			_enter_state(State.LANDING)
			emit_signal("landed")

		# Consumir jump buffer si había uno guardado
		if jump_buffer_timer > 0.0:
			jump_buffer_timer = 0.0
			_do_jump()

	# Caer desde un borde
	if was_on_floor and not is_on_floor():
		if current_state == State.IDLE or current_state == State.RUNNING:
			_enter_state(State.FALLING)


func _check_jump_input() -> void:
	if Input.is_action_just_pressed("jump"):
		var can_coyote = not coyote_timer.is_stopped()
		if is_on_floor() or can_coyote:
			_do_jump()
		else:
			jump_buffer_timer = jump_buffer  # guardar para cuando aterrice


func _do_jump() -> void:
	velocity.y = jump_force
	coyote_timer.stop()
	_enter_state(State.JUMPING)
	emit_signal("jumped")


# ==================================================================
# ENTRADA Y SALIDA DE ESTADOS
# ==================================================================
func _enter_state(new_state: State) -> void:
	if new_state == current_state:
		return

	_exit_state(current_state)
	var old = current_state
	current_state = new_state
	emit_signal("state_changed", old, new_state)

	match new_state:
		State.IDLE:       _play_anim("idle")
		State.RUNNING:    _play_anim("run")
		State.JUMPING:    _play_anim("jump")
		State.FALLING:    _play_anim("fall")
		State.LANDING:    _play_anim("landing")
		State.WALL_SLIDE: _play_anim("wall_slide")
		State.HURT:
			_play_anim("hurt")
			hurt_timer.start(hurt_duration)
			inv_timer.start(invincibility_time)
			is_invincible = true
			inv_timer.timeout.connect(func(): is_invincible = false, CONNECT_ONE_SHOT)
		State.DEAD:
			_play_anim("death")
			hitbox.set_deferred("disabled", true)
			emit_signal("died")


func _exit_state(old_state: State) -> void:
	pass  # Lógica de limpieza al salir (ej: detener partículas)


# ==================================================================
# MOVIMIENTO HORIZONTAL — con aceleración/desaceleración
# ==================================================================
func _apply_horizontal(direction: float, delta: float) -> void:
	if direction != 0.0:
		velocity.x = move_toward(velocity.x, direction * run_speed, acceleration * delta)
	else:
		velocity.x = move_toward(velocity.x, 0.0, deceleration * delta)


func _update_facing(direction: float) -> void:
	if direction > 0.0 and not facing_right:
		facing_right = true
		sprite.flip_h = false
	elif direction < 0.0 and facing_right:
		facing_right = false
		sprite.flip_h = true


func _is_touching_wall() -> bool:
	if not has_node("WallCheckerLeft") or not has_node("WallCheckerRight"):
		return is_on_wall()
	return wall_checker_l.is_colliding() or wall_checker_r.is_colliding()


func _play_anim(anim_name: String) -> void:
	if sprite and sprite.sprite_frames and sprite.sprite_frames.has_animation(anim_name):
		sprite.play(anim_name)


# ==================================================================
# SISTEMA DE DAÑO (llamado desde enemigos, trampas, etc.)
# ==================================================================
func take_damage(amount: int, knockback_direction: Vector2 = Vector2.LEFT) -> void:
	if is_invincible or current_state == State.DEAD:
		return

	health -= amount
	emit_signal("health_changed", health, max_health)

	velocity = knockback_direction.normalized() * hurt_knockback
	_enter_state(State.HURT)

	if health <= 0:
		_enter_state(State.DEAD)


# ==================================================================
# DEBUG — muestra estado actual en pantalla (quitar en build final)
# ==================================================================
func _draw() -> void:
	if OS.is_debug_build():
		var label = State.keys()[current_state]
		# En Godot 4 puedes usar un Label nodo hijo en su lugar
		pass
