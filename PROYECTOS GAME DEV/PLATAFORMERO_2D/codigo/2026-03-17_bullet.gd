## ============================================================
## MECÁNICA: Bala / Proyectil (Plataformero 2D)
## Generado: 17 de marzo 2026 | Semana 1 | Fase: Fundamentos
## Motor: Godot 4 / GDScript
## Para: Bruno — Indie Dev Portfolio | UANL Monterrey
## ============================================================
##
## ESTE SCRIPT va en tu escena Bullet.tscn
## Nodo raíz: Area2D (renómbralo "Bullet")
##
## CÓMO CREAR Bullet.tscn:
##   1. Archivo > Nueva Escena
##   2. Nodo raíz: Area2D → renombrar a "Bullet"
##   3. Hijo 1: CollisionShape2D → CircleShape2D (radio ~4)
##   4. Hijo 2: Sprite2D → asigna 2026-03-17_bala_jugador.png
##      (o usa ColorRect si no tienes sprite listo)
##   5. Adjunta ESTE script al nodo Area2D
##   6. Guarda como res://scenes/Bullet.tscn
## ============================================================

extends Area2D

## ---- VARIABLES EXPORTABLES ----
@export var speed: float = 500.0        ## Velocidad en píxeles/segundo
@export var lifetime: float = 2.0       ## Segundos antes de auto-destruirse
@export var damage: int = 1             ## Daño al impactar enemigos

## ---- VARIABLES INTERNAS ----
var direction: float = 1.0              ## +1 = derecha, -1 = izquierda (asignado por el jugador)
var _elapsed: float = 0.0              ## Tiempo transcurrido desde que se creó


func _ready() -> void:
	# Conectamos la señal: cuando algo entra al área de la bala
	body_entered.connect(_on_body_entered)
	area_entered.connect(_on_area_entered)

	# Efecto visual: aparece con pequeña animación de escala
	scale = Vector2(0.1, 0.1)
	var tween = create_tween()
	tween.tween_property(self, "scale", Vector2(1.0, 1.0), 0.05)


func _physics_process(delta: float) -> void:
	# ---- MOVIMIENTO ----
	# Mueve la bala horizontalmente según su dirección
	position.x += speed * direction * delta

	# ---- TIEMPO DE VIDA ----
	_elapsed += delta
	if _elapsed >= lifetime:
		_destroy()

	# ---- SALIR DE PANTALLA ----
	# Si la bala sale de la pantalla visible, la destruimos
	var screen_size = get_viewport().get_visible_rect().size
	if position.x < -50 or position.x > screen_size.x + 50:
		_destroy()


## _on_body_entered() — cuando la bala toca un CharacterBody2D o StaticBody2D
func _on_body_entered(body: Node2D) -> void:
	# Si golpea un enemigo (que tenga grupo "enemies")
	if body.is_in_group("enemies"):
		if body.has_method("take_damage"):
			body.take_damage(damage)
		_spawn_hit_effect()
		_destroy()
		return

	# Si golpea el suelo u obstáculo (no es el jugador)
	if not body.is_in_group("player"):
		_spawn_hit_effect()
		_destroy()


## _on_area_entered() — cuando toca otra Area2D (como hitbox de enemigos)
func _on_area_entered(area: Area2D) -> void:
	if area.is_in_group("enemy_hitbox"):
		var enemy = area.get_parent()
		if enemy.has_method("take_damage"):
			enemy.take_damage(damage)
		_spawn_hit_effect()
		_destroy()


## _spawn_hit_effect() — efecto visual al impactar (opcional)
func _spawn_hit_effect() -> void:
	# Efecto simple: flash de color antes de destruirse
	# Para un efecto más elaborado, instancia un GPUParticles2D aquí
	var flash = ColorRect.new()
	flash.size = Vector2(16, 16)
	flash.position = Vector2(-8, -8)
	flash.color = Color(1.0, 0.9, 0.3, 0.8)  # Amarillo brillante
	add_child(flash)

	var tween = create_tween()
	tween.tween_property(flash, "modulate:a", 0.0, 0.1)
	tween.tween_callback(flash.queue_free)


## _destroy() — limpieza segura antes de queue_free
func _destroy() -> void:
	# Desactivar colisión para evitar múltiples hits
	set_deferred("monitoring", false)
	set_deferred("monitorable", false)
	queue_free()


# ============================================================
# PARA AGREGAR SONIDO DE DISPARO:
#
# 1. En Bullet.tscn agrega un hijo: AudioStreamPlayer2D
# 2. Asígna un .ogg o .wav de disparo
# 3. En _ready() agrega: $AudioStreamPlayer2D.play()
#
# PARA VARIACIONES DE BALA (sin cambiar este script):
# - Bala rápida: speed = 800, damage = 1
# - Bala lenta pesada: speed = 200, damage = 3, scale más grande
# - Bala que rebota: override _on_body_entered para cambiar direction
#
# MEJORA FUTURA: Sistema de armas (weapon_system.gd)
# - Pistola, escopeta (múltiples balas en spread), rifle
# ============================================================
