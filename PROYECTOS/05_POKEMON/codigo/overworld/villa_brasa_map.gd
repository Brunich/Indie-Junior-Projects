## VillaBrasaMap — VILLA BRASA, Pueblo Inicial
## Pueblo norteño-mexicano de partida. Terracería, casas de adobe, altares, plaza central.
## Izel comienza aquí. Nana Remi vive al este. Temazcal al oeste. La Tienda al norte-este.
## Salidas: norte → La Sierra Ruta 1 | sur → camino de terracería (tall grass, primeros Nexos).
## 50×32 tiles @ 16px = 800×512 píxeles de mundo.
extends TileMapLayer

# ── Atlas coords — Serene Village - Outside.png (8×27 tiles de 16px) ──────────
# Ejecuta res://codigo/herramientas/create_tileset_serene_village.gd en el editor
# para crear el recurso TileSet automáticamente.
const T_GRASS    := Vector2i(0, 0)   # césped verde oscuro (piso principal)
const T_GRASS_L  := Vector2i(1, 0)   # pasto claro / transición
const T_SAND     := Vector2i(6, 0)   # arena / tierra seca
const T_GROUND   := Vector2i(1, 1)   # tierra descubierta
const T_PATH     := Vector2i(2, 2)   # camino de terracería / adoquín
const T_TALL     := Vector2i(0, 3)   # pasto alto — zona de encuentros
const T_WATER_TL := Vector2i(3, 0)   # agua esquina sup-izq
const T_WATER_T  := Vector2i(4, 0)   # agua borde superior
const T_WATER_TR := Vector2i(5, 0)   # agua esquina sup-der
const T_WATER_L  := Vector2i(3, 1)   # agua borde izquierdo
const T_WATER_C  := Vector2i(4, 1)   # agua centro (fuente)
const T_WATER_R  := Vector2i(5, 1)   # agua borde derecho
const T_WATER_BL := Vector2i(3, 2)   # agua esquina inf-izq
const T_WATER_B  := Vector2i(4, 2)   # agua borde inferior
const T_WATER_BR := Vector2i(5, 2)   # agua esquina inf-der
const T_TREE_TL  := Vector2i(0, 4)   # copa de árbol sup-izq (BLOQUEANTE)
const T_TREE_TR  := Vector2i(1, 4)   # copa de árbol sup-der
const T_TREE_BL  := Vector2i(0, 5)   # tronco / arbusto inf-izq
const T_TREE_BR  := Vector2i(1, 5)   # tronco / arbusto inf-der
const T_FENCE_H  := Vector2i(1, 6)   # cerca horizontal
const T_FENCE_P  := Vector2i(0, 6)   # poste de cerca
const T_BLDG_R   := Vector2i(0, 8)   # techo rojo — Lab, Tienda (edificios institucionales)
const T_BLDG_W   := Vector2i(0,10)   # pared roja — Lab, Tienda
const T_BLDG_R2  := Vector2i(0,13)   # techo verde — casas habitación (Izel, Nana Remi)
const T_BLDG_W2  := Vector2i(0,15)   # pared verde — casas habitación
const T_BLDG_R3  := Vector2i(0,18)   # techo azul — Temazcal (lugar sagrado/curación)
const T_BLDG_W3  := Vector2i(0,20)   # pared azul — Temazcal
const T_ALTAR    := Vector2i(3, 4)   # altar / señal decorativa
const T_BORDER   := Vector2i(0, 4)   # borde mapa (mismo que árbol)

# ── Tabla de caracteres → coordenadas de atlas ────────────────────────────────
const CHAR_TO_ATLAS := {
	"R": T_BORDER,   "g": T_GRASS,    "G": T_GROUND,   "s": T_SAND,
	"T": T_TALL,     "P": T_PATH,     ".": T_GROUND,   "~": T_WATER_L,
	"W": T_WATER_C,  "t": T_TREE_TL,  "r": T_TREE_BL,  "B": T_BLDG_R,
	"b": T_BLDG_W,   "H": T_BLDG_R2,  "h": T_BLDG_W2,  "C": T_BLDG_R3,
	"c": T_BLDG_W3,  "F": T_FENCE_H,  "f": T_FENCE_P,  "A": T_ALTAR,
}

# ── Mapa de Villa Brasa (50×32) ───────────────────────────────────────────────
# Leyenda:
#   R=borde  g=pasto  T=pasto-alto  P=camino  .=tierra-plaza
#   t=árbol-copa  r=árbol-tronco  B=techo  b=pared
#   W=agua(fuente)  ~=borde-agua  A=altar  F=cerca
#
# Estructura de columnas (0-indexed):
#   Col 0 y 49 = borde R
#   Ruta norte (exit): cols 21-23
#   Edificios norte: Lab cols 4-12 | Tienda cols 29-39
#   Camino vertical: cols 21-23 (alineado norte-sur)
#   Edificios sur: Temazcal cols 2-10 | Casa Izel cols 12-20 | Nana Remi cols 31-43
#   Tall grass + salida sur: rows 27-29
const MAP := [
# col  0         1         2         3         4
#      0123456789012345678901234567890123456789012345678 9
	"RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",  # row  0  borde norte
	"RtttttttttttttttttttttPPPtttttttttttttttttttttttR",  # row  1  árboles (Ruta 1 sale aquí)
	"RtrrttttttttttttttttttPPPtttttttttttttttrrtttttttR",  # row  2  troncos + apertura Ruta 1
	"RgggggggggggggggggggggPPPgggggggggggggggggggggggggR",  # row  3  pasto abierto norte
	"RgggBBBBBBBBBggggggggPPPggggBBBBBBBBBBBgggggggggR",  # row  4  [Lab Guía] | [Tienda]
	"RgggBBBBBBBBBggggggggPPPggggBBBBBBBBBBBgggggggggR",  # row  5
	"RgggBBBBBBBBBggggggggPPPggggBBBBBBBBBBBgggggggggR",  # row  6
	"RgggbbbbbbbbbggggggggPPPggggbbbbbbbbbbbgggggggggR",  # row  7  paredes norte
	"RgggbbbbbbbbbggggggggPPPggggbbbbbbbbbbbgggggggggR",  # row  8
	"RgggggggggggggggggggggPPPgggggggggggggggggggggggggR",  # row  9  separador norte
	"RPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPr",  # row 10  CAMINO EO principal (terracería)
	"RPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPR",  # row 11
	"RgggggggggggggggggggggPPPgggggggggggggggggggggggggR",  # row 12  conector plaza
	"RgggggPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPgggggggR",  # row 13  entrada plaza (corredor)
	"Rggggg...............PPP.................gggggggR",  # row 14  plaza oeste + este
	"Rggggg....A.........PPP.........A.......gggggggR",  # row 15  ALTARES (A) flanqueando camino
	"Rggggg....~WWW......PPP......WWW~.......gggggggR",  # row 16  FUENTE (W) — plaza central
	"Rggggg....~WWW......PPP......WWW~.......gggggggR",  # row 17
	"Rggggg...............PPP.................gggggggR",  # row 18  plaza cierre
	"RgggggggggggggggggggggPPPgggggggggggggggggggggggggR",  # row 19  separador sur
	"RgCCCCCCCCCgHHHHHHHHHPPPgggggggHHHHHHHHHHHHHHggggR",  # row 20  [Temazcal azul][Izel verde][NanaRemi verde]
	"RgCCCCCCCCCgHHHHHHHHHPPPgggggggHHHHHHHHHHHHHHggggR",  # row 21
	"RgCCCCCCCCCgHHHHHHHHHPPPgggggggHHHHHHHHHHHHHHggggR",  # row 22
	"RgcccccccccghhhhhhhhhPPPggggggghhhhhhhhhhhhhhggggR",  # row 23  paredes sur
	"RgcccccccccghhhhhhhhhPPPggggggghhhhhhhhhhhhhhggggR",  # row 24
	"RgfgggggggfgfgggggggfPPPgggggggggggggggggggggggggR",  # row 25  cercas en esquinas de Temazcal e Izel
	"RgggggggggggggggggggggPPPgggggggggggggggggggggggggR",  # row 26
	"RTTTTTTTTTTTTTTTTTTTTTPPPTTTTTTTTTTTTTTTTTTTTTTR",  # row 27  PASTO ALTO — encuentros!
	"RTTTTTTTTTTTTTTTTTTTTTPPPTTTTTTTTTTTTTTTTTTTTTTR",  # row 28  segunda fila tall grass
	"RgggggggggggggggggggggPPPgggggggggggggggggggggggggR",  # row 29  camino de salida sur
	"RgggggggggggggggggggggPPPgggggggggggggggggggggggggR",  # row 30
	"RRRRRRRRRRRRRRRRRRRRRRPPPRRRRRRRRRRRRRRRRRRRRRRRR",  # row 31  borde sur (salida a Ruta 1-S)
]

# ── Dimensiones ────────────────────────────────────────────────────────────────
const MAP_WIDTH  := 50
const MAP_HEIGHT := 32

# ── Puntos de aparición (tile coords) ─────────────────────────────────────────
var spawn_points := {
	"default":          Vector2i(22, 29),  # entrada sur por defecto
	"from_ruta1_norte": Vector2i(22,  3),  # viene de Ruta 1 Norte
	"from_ruta1_sur":   Vector2i(22, 29),  # viene de camino sur
	"temazcal_exit":    Vector2i( 6, 24),  # sale del Temazcal
	"izel_home_exit":   Vector2i(16, 24),  # sale de Casa Izel
	"nana_remi_exit":   Vector2i(37, 24),  # sale de casa Nana Remi
	"tienda_exit":      Vector2i(34,  8),  # sale de la Tienda
	"lab_exit":         Vector2i( 8,  8),  # sale del Lab/Guía
}

# ── Posiciones clave en el mapa ────────────────────────────────────────────────
const TEMAZCAL_TILE     := Vector2i( 6, 20)   # Temazcal — curación (Pokémon Center)
const IZEL_HOME_TILE    := Vector2i(16, 20)   # Casa de Izel — inicio de la historia
const NANA_REMI_TILE    := Vector2i(37, 20)   # Nana Remi / Luzma — guía de inicio
const LAB_TILE          := Vector2i( 8,  4)   # Asistente de Lab / figura inicial
const TIENDA_TILE       := Vector2i(34,  4)   # Tienda — compra/venta
const ALTAR_OESTE_TILE  := Vector2i(10, 15)   # Altar oeste de la plaza
const ALTAR_ESTE_TILE   := Vector2i(37, 15)   # Altar este de la plaza
const FUENTE_TILE       := Vector2i(25, 16)   # Fuente central

# ── Posiciones de NPCs ─────────────────────────────────────────────────────────
const NPC_POSITIONS := {
	"nana_remi":    NANA_REMI_TILE,
	"luzma":        Vector2i(11, 16),   # Luzma — guardiana de altares (junto al altar oeste, en la plaza)
	"tavo_rival":   Vector2i(22, 13),   # Tavo — rival, en el corredor de la plaza
	"tendero":      Vector2i(34,  6),   # Tendero
	"sanadora":     Vector2i( 6, 22),   # Sanadora del Temazcal
	"vecino_viejo": Vector2i(16, 18),   # Vecino en la plaza
	"muchacho":     Vector2i(28,  3),   # Chico cerca de la tienda (norte)
}

# ── Tabla de encuentros (pasto alto — zona sur) ────────────────────────────────
# Nexos de La Sierra del Norte: tierra/fuego, lentos en vincularse
const ENCOUNTER_TABLE := {
	"embral":      35,   # Inicio línea de fuego, común en la sierra
	"popocardon":  25,   # Tipo tierra/cactus, norteño
	"carabronte":  20,   # Tipo tierra, caparazón duro
	"sierraptor":  15,   # Tipo roca/vuelo, pájaro serrano
	"xolcan":       5,   # Tipo volcánico, raro
}
const ENCOUNTER_LEVEL_MIN := 2
const ENCOUNTER_LEVEL_MAX := 5

# ─────────────────────────────────────────────────────────────────────────────
func _ready() -> void:
	_build_map()

func _build_map() -> void:
	for row in MAP.size():
		var line := MAP[row]
		for col in mini(line.length(), MAP_WIDTH):
			var ch    := line.substr(col, 1)
			var atlas := CHAR_TO_ATLAS.get(ch, T_GRASS)
			set_cell(Vector2i(col, row), 0, atlas)

## Devuelve posición mundial desde un ID de spawn
func get_spawn_world_pos(spawn_id: String) -> Vector2:
	var tile := spawn_points.get(spawn_id, spawn_points["default"])
	return map_to_local(tile)

## Zoom de cámara preferido (estilo Pokémon 2×)
func get_preferred_camera_zoom() -> Vector2:
	return Vector2(2.0, 2.0)

## Devuelve un encuentro aleatorio ponderado del pasto alto
func random_encounter(level_override: int = -1) -> Dictionary:
	var roll := randi() % 100
	var cumulative := 0
	for id: String in ENCOUNTER_TABLE:
		cumulative += ENCOUNTER_TABLE[id]
		if roll < cumulative:
			var lvl := level_override if level_override > 0 \
				else randi_range(ENCOUNTER_LEVEL_MIN, ENCOUNTER_LEVEL_MAX)
			return {"id": id, "level": lvl}
	return {"id": "embral", "level": ENCOUNTER_LEVEL_MIN}
