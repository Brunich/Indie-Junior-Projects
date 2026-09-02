extends Node2D

const CELL := 48
const GRID_W := 15
const GRID_H := 11

@onready var board: Node2D = $Board
@onready var hud: Label = $UI/HUD

var grid: Array = []
var floor_num := 1
var player_hp := 5
var player_pos := Vector2i(1, 1)
var enemies: Array[Dictionary] = []
var _busy := false


func _ready() -> void:
	randomize()
	_new_floor()


func _new_floor() -> void:
	grid = DungeonGen.generate(GRID_W, GRID_H, 0.28 + floor_num * 0.02)
	player_pos = Vector2i(1, 1)
	enemies.clear()
	var avoid: Array[Vector2i] = [player_pos, Vector2i(GRID_W - 2, GRID_H - 2)]
	var count := mini(3 + floor_num, 8)
	for _i in count:
		var pos := DungeonGen.random_floor_tile(grid, avoid)
		avoid.append(pos)
		enemies.append({"pos": pos, "hp": 2 + floor_num / 2})
	_refresh_view()


func _refresh_view() -> void:
	for child in board.get_children():
		child.queue_free()

	for y in GRID_H:
		for x in GRID_W:
			var tile: int = grid[y][x]
			var rect := ColorRect.new()
			rect.size = Vector2(CELL - 2, CELL - 2)
			rect.position = Vector2(x * CELL + 1, y * CELL + 1)
			match tile:
				DungeonGen.Tile.WALL:
					rect.color = Color(0.18, 0.2, 0.28)
				DungeonGen.Tile.EXIT:
					rect.color = Color(0.95, 0.75, 0.2)
				_:
					rect.color = Color(0.1, 0.12, 0.16)
			board.add_child(rect)

	for enemy in enemies:
		_spawn_marker(enemy.pos, Color(0.95, 0.35, 0.4), CELL * 0.55)

	_spawn_marker(player_pos, Color(0.45, 0.85, 1.0), CELL * 0.65)
	_update_hud()


func _spawn_marker(cell: Vector2i, color: Color, size: float) -> void:
	var rect := ColorRect.new()
	rect.size = Vector2(size, size)
	rect.position = Vector2(cell.x * CELL + (CELL - size) * 0.5, cell.y * CELL + (CELL - size) * 0.5)
	rect.color = color
	board.add_child(rect)


func _update_hud() -> void:
	hud.text = "Piso %d  |  HP %d  |  Enemigos %d  |  WASD mover · R reiniciar" % [
		floor_num, player_hp, enemies.size()
	]


func _unhandled_input(event: InputEvent) -> void:
	if _busy:
		return
	if event.is_action_pressed("move_up"):
		_try_move(Vector2i.UP)
	elif event.is_action_pressed("move_down"):
		_try_move(Vector2i.DOWN)
	elif event.is_action_pressed("move_left"):
		_try_move(Vector2i.LEFT)
	elif event.is_action_pressed("move_right"):
		_try_move(Vector2i.RIGHT)
	elif event is InputEventKey and event.pressed and event.keycode == KEY_R:
		get_tree().reload_current_scene()


func _try_move(dir: Vector2i) -> void:
	var next := player_pos + dir
	if not DungeonGen.is_walkable(grid, next):
		return

	var enemy_idx := _enemy_at(next)
	if enemy_idx >= 0:
		enemies[enemy_idx]["hp"] -= 1
		if enemies[enemy_idx]["hp"] <= 0:
			enemies.remove_at(enemy_idx)
		else:
			_damage_player(1)
	else:
		player_pos = next
		if grid[next.y][next.x] == DungeonGen.Tile.EXIT:
			floor_num += 1
			_new_floor()
			return

	_enemy_turn()
	_refresh_view()

	if player_hp <= 0:
		_game_over()


func _enemy_at(cell: Vector2i) -> int:
	for i in enemies.size():
		if enemies[i]["pos"] == cell:
			return i
	return -1


func _enemy_turn() -> void:
	for enemy in enemies:
		var options: Array[Vector2i] = []
		for dir in DungeonGen.DIRS:
			var next := enemy.pos + dir
			if next == player_pos:
				_damage_player(1)
				return
			if DungeonGen.is_walkable(grid, next) and _enemy_at(next) < 0 and next != player_pos:
				options.append(next)
		if options.is_empty():
			continue
		options.shuffle()
		enemy.pos = options[0]


func _damage_player(amount: int) -> void:
	player_hp -= amount


func _game_over() -> void:
	_busy = true
	hud.text = "Game Over — llegaste al piso %d — R reiniciar" % floor_num
