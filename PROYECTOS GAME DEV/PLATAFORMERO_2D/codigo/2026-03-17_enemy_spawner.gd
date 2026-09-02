## EnemySpawner.gd — Genera enemigos en puntos de spawn definidos en el nivel
## Colocar como nodo hijo del nivel. Añadir SpawnPoint (Marker2D) como hijos.
extends Node

@export var enemy_scene: PackedScene
## Máximo de enemigos simultáneos en pantalla
@export var max_enemies: int = 5
## Tiempo entre spawns en segundos
@export var spawn_interval: float = 4.0
## Solo el servidor genera enemigos en multiplayer
@export var server_only: bool = true

var _active_enemies: Array[Node] = []
var _spawn_timer: float = 0.0
var _spawn_points: Array[Node2D] = []

func _ready() -> void:
    # Recopilar todos los Marker2D hijos como puntos de spawn
    for child in get_children():
        if child is Marker2D:
            _spawn_points.append(child)
    if _spawn_points.is_empty():
        push_warning("EnemySpawner: no se encontraron SpawnPoints (Marker2D)")

func _process(delta: float) -> void:
    # En multiplayer, solo el servidor spawna
    if server_only and multiplayer.has_multiplayer_peer():
        if not multiplayer.is_server():
            return

    _spawn_timer += delta
    if _spawn_timer >= spawn_interval:
        _spawn_timer = 0.0
        _try_spawn()

func _try_spawn() -> void:
    # Limpiar enemigos muertos del array
    _active_enemies = _active_enemies.filter(func(e): return is_instance_valid(e))
    
    if _active_enemies.size() >= max_enemies:
        return
    if _spawn_points.is_empty() or not enemy_scene:
        return

    # Elegir punto de spawn aleatorio
    var point: Node2D = _spawn_points[randi() % _spawn_points.size()]
    var enemy := enemy_scene.instantiate()
    get_parent().add_child(enemy)
    enemy.global_position = point.global_position
    _active_enemies.append(enemy)

## Detener spawning (útil en pausa o game over)
func stop() -> void:
    set_process(false)

func resume() -> void:
    set_process(true)
