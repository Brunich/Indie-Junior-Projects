extends RefCounted
class_name DungeonGen

enum Tile { FLOOR, WALL, EXIT }

const DIRS := [Vector2i.UP, Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT]


static func generate(width: int, height: int, fill: float = 0.32) -> Array:
	var grid: Array = []
	for y in height:
		var row: Array = []
		for x in width:
			var edge := x == 0 or y == 0 or x == width - 1 or y == height - 1
			row.append(Tile.WALL if edge or randf() < fill else Tile.FLOOR)
		grid.append(row)

	grid[1][1] = Tile.FLOOR
	grid[height - 2][width - 2] = Tile.EXIT
	_carve_path(grid, Vector2i(1, 1), Vector2i(width - 2, height - 2))
	return grid


static func _carve_path(grid: Array, start: Vector2i, goal: Vector2i) -> void:
	var current := start
	grid[current.y][current.x] = Tile.FLOOR
	while current != goal:
		var step := Vector2i(
			clampi(goal.x - current.x, -1, 1),
			clampi(goal.y - current.y, -1, 1)
		)
		if step == Vector2i.ZERO:
			break
		if absi(goal.x - current.x) > absi(goal.y - current.y):
			step.y = 0
		else:
			step.x = 0
		current += step
		grid[current.y][current.x] = Tile.FLOOR


static func random_floor_tile(grid: Array, avoid: Array[Vector2i]) -> Vector2i:
	var width: int = grid[0].size()
	var height: int = grid.size()
	for _i in 200:
		var pos := Vector2i(randi_range(1, width - 2), randi_range(1, height - 2))
		if grid[pos.y][pos.x] == Tile.FLOOR and not avoid.has(pos):
			return pos
	return Vector2i(1, 1)


static func is_walkable(grid: Array, pos: Vector2i) -> bool:
	if pos.x < 0 or pos.y < 0 or pos.y >= grid.size() or pos.x >= grid[0].size():
		return false
	return grid[pos.y][pos.x] != Tile.WALL
