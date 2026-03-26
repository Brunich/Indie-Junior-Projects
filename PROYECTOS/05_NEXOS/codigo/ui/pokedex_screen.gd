## PokedexScreen — Registro de criaturas con lista y ficha detallada.
## Unknown creatures show as black silhouettes with "???".
## Discovered set is stored in GameManager arrays: seen_ids / caught_ids.
class_name PokedexScreen extends Control

const RuntimeTextureLoader = preload("res://codigo/util/runtime_texture_loader.gd")

# ── Node refs ─────────────────────────────────────────────────────────────────
@onready var grid_view       : Control        = $layout/grid_view
@onready var detail_view     : Control        = $layout/detail_view
@onready var grid_container  : GridContainer  = $layout/grid_view/scroll/grid
@onready var filter_bar      : HBoxContainer  = $layout/grid_view/filter_bar
@onready var search_field    : LineEdit        = $layout/grid_view/filter_bar/search
@onready var count_label     : Label          = $layout/grid_view/count_label

# Detail view nodes
@onready var detail_sprite   : TextureRect    = $layout/detail_view/left/sprite
@onready var detail_number   : Label          = $layout/detail_view/left/number
@onready var detail_name     : Label          = $layout/detail_view/left/name_label
@onready var detail_category : Label          = $layout/detail_view/left/category
@onready var detail_type_row : HBoxContainer  = $layout/detail_view/left/type_row
@onready var detail_desc     : Label          = $layout/detail_view/right/desc
@onready var detail_stats    : VBoxContainer  = $layout/detail_view/right/stats
@onready var detail_evol     : HBoxContainer  = $layout/detail_view/right/evol_chain
@onready var detail_seen_txt : Label          = $layout/detail_view/left/seen_txt
@onready var btn_back        : Button         = $layout/detail_view/right/btn_back
@onready var btn_prev        : Button         = $layout/detail_view/right/btn_prev
@onready var btn_next_entry  : Button         = $layout/detail_view/right/btn_next_entry

const SPRITE_PATH    = "res://sprites/nexos/"
const SILHOUETTE_MOD = Color(0, 0, 0, 1)   ## Black modulate for unknown

var _current_index : int = 0
var _filtered_ids  : Array = []

# ─────────────────────────────────────────────────────────────────────────────
func _ready() -> void:
	search_field.text_changed.connect(_on_search_changed)
	btn_back.pressed.connect(_on_back_pressed)
	btn_prev.pressed.connect(func(): _navigate(-1))
	btn_next_entry.pressed.connect(func(): _navigate(1))
	refresh()

func refresh() -> void:
	_filtered_ids = PokedexData.get_all_ids()
	_build_grid()
	_update_count()
	grid_view.show()
	detail_view.hide()

# ── Grid ──────────────────────────────────────────────────────────────────────
func _build_grid() -> void:
	for child in grid_container.get_children(): child.queue_free()
	await get_tree().process_frame

	for id in _filtered_ids:
		var entry   = PokedexData.get_entry(id)
		var seen    = id in GameManager.seen_ids
		var caught  = id in GameManager.caught_ids
		var card    = _build_card(entry, seen, caught)
		grid_container.add_child(card)

func _build_card(entry: Dictionary, seen: bool, caught: bool) -> PanelContainer:
	var panel = PanelContainer.new()
	panel.custom_minimum_size = Vector2(72, 88)

	var style = StyleBoxFlat.new()
	style.bg_color       = Color(0.10, 0.10, 0.16)
	style.corner_radius_top_left = 8
	style.corner_radius_top_right = 8
	style.corner_radius_bottom_left = 8
	style.corner_radius_bottom_right = 8
	style.border_width_top = 2
	style.border_width_bottom = 2
	style.border_width_left = 2
	style.border_width_right = 2
	style.border_color   = Color(0.3, 0.3, 0.5) if not caught else Color(0.6, 0.4, 0.0)
	panel.add_theme_stylebox_override("panel", style)

	var vbox = VBoxContainer.new()
	panel.add_child(vbox)

	# Number
	var num_lbl = Label.new()
	num_lbl.text = "#%03d" % entry.get("number", 0)
	num_lbl.add_theme_font_size_override("font_size", 9)
	num_lbl.add_theme_color_override("font_color", Color(0.5, 0.5, 0.6))
	num_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vbox.add_child(num_lbl)

	# Sprite / silhouette
	var sprite = TextureRect.new()
	sprite.custom_minimum_size  = Vector2(48, 48)
	sprite.stretch_mode         = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	sprite.expand_mode          = TextureRect.EXPAND_FIT_WIDTH_PROPORTIONAL
	sprite.size_flags_horizontal = Control.SIZE_SHRINK_CENTER

	if seen:
		var tex = _load_creature_sprite(String(entry["id"]))
		sprite.texture  = tex
		sprite.modulate = Color(1, 1, 1, 1)
	else:
		var tex = _load_creature_sprite(String(entry["id"]))
		sprite.texture  = tex
		sprite.modulate = SILHOUETTE_MOD
	vbox.add_child(sprite)

	# Name
	var name_lbl = Label.new()
	name_lbl.text = entry["name"] if seen else "???"
	name_lbl.add_theme_font_size_override("font_size", 10)
	name_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	name_lbl.add_theme_color_override("font_color",
		Color(1, 1, 1) if seen else Color(0.4, 0.4, 0.4))
	vbox.add_child(name_lbl)

	# Marker if caught
	if caught:
		var ball_lbl = Label.new()
		ball_lbl.text = "●"
		ball_lbl.add_theme_color_override("font_color", Color(1, 0.4, 0.4))
		ball_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		ball_lbl.add_theme_font_size_override("font_size", 8)
		vbox.add_child(ball_lbl)

	# Click to open detail
	var btn = Button.new()
	btn.flat = true
	btn.anchor_right  = 1.0
	btn.anchor_bottom = 1.0
	panel.add_child(btn)
	if seen:
		var idx = _filtered_ids.find(entry["id"])
		btn.pressed.connect(func(): _open_detail(idx))

	return panel

# ── Detail view ───────────────────────────────────────────────────────────────
func _open_detail(index: int) -> void:
	_current_index = index
	_populate_detail(index)
	grid_view.hide()
	detail_view.show()

func _populate_detail(index: int) -> void:
	var id    = _filtered_ids[index]
	var entry = PokedexData.get_entry(id)
	var caught = id in GameManager.caught_ids
	var seen   = id in GameManager.seen_ids

	# Sprite
	var tex = _load_creature_sprite(id)
	if detail_sprite:
		detail_sprite.texture  = tex
		detail_sprite.modulate = Color(1,1,1)

	# Identity
	detail_number.text   = "#%03d" % entry.get("number", 0)
	detail_name.text     = entry.get("name", id.capitalize())
	detail_category.text = entry.get("category", "")

	# Types
	for child in detail_type_row.get_children(): child.queue_free()
	await get_tree().process_frame
	for type_str in [entry.get("type1",""), entry.get("type2","")]:
		if type_str == "": continue
		var badge = Label.new()
		badge.text = type_str.to_upper()
		badge.add_theme_color_override("font_color", PokedexData.type_color(type_str))
		badge.add_theme_font_size_override("font_size", 12)
		detail_type_row.add_child(badge)

	# Description & flavor
	detail_desc.text = entry.get("description", "") + \
	                   ("\n\nHeight: %.1fm  Weight: %.1fkg" % [entry.get("height",0.0), entry.get("weight",0.0)])

	# Seen / caught status
	var status_str = "SIN REGISTRO"
	if caught: status_str = "VINCULADA ●"
	elif seen: status_str = "VISTA ◦"
	if detail_seen_txt: detail_seen_txt.text = status_str

	# Base stats mini-bars
	for child in detail_stats.get_children(): child.queue_free()
	await get_tree().process_frame

	var base = entry.get("base", {})
	for kv in [["HP", "hp"], ["Atk", "atk"], ["Def", "def"],
	           ["SpA", "spatk"], ["SpD", "spdef"], ["Spd", "spd"]]:
		var label_txt = kv[0]
		var key       = kv[1]
		var val       = base.get(key, 50) as int
		_add_mini_stat(label_txt, val)

	# Evolution chain
	for child in detail_evol.get_children(): child.queue_free()
	await get_tree().process_frame

	var chain = entry.get("evolution", [id])
	for i in chain.size():
		var evo_id  = chain[i]
		var evo_tex = _load_creature_sprite(evo_id)
		var evo_box = VBoxContainer.new()
		evo_box.custom_minimum_size = Vector2(52, 0)
		detail_evol.add_child(evo_box)

		var evo_sprite = TextureRect.new()
		evo_sprite.custom_minimum_size = Vector2(48, 48)
		evo_sprite.texture = evo_tex
		evo_sprite.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		evo_box.add_child(evo_sprite)

		var evo_lbl = Label.new()
		evo_lbl.text = PokedexData.get_entry(evo_id).get("name", evo_id.capitalize())
		evo_lbl.add_theme_font_size_override("font_size", 9)
		evo_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		evo_box.add_child(evo_lbl)

		if i < chain.size() - 1:
			var arrow = Label.new()
			arrow.text = "→"
			arrow.add_theme_font_size_override("font_size", 18)
			arrow.add_theme_color_override("font_color", Color(0.5, 0.5, 0.5))
			detail_evol.add_child(arrow)

func _add_mini_stat(label: String, value: int) -> void:
	var hbox = HBoxContainer.new()
	detail_stats.add_child(hbox)

	var lbl = Label.new()
	lbl.text = label
	lbl.custom_minimum_size = Vector2(36, 0)
	lbl.add_theme_font_size_override("font_size", 10)
	lbl.add_theme_color_override("font_color", Color(0.7, 0.7, 0.7))
	hbox.add_child(lbl)

	var val_lbl = Label.new()
	val_lbl.text = str(value)
	val_lbl.custom_minimum_size = Vector2(28, 0)
	val_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	val_lbl.add_theme_font_size_override("font_size", 10)
	hbox.add_child(val_lbl)

	var bar = ProgressBar.new()
	bar.min_value = 0; bar.max_value = 255; bar.value = value
	bar.show_percentage = false
	bar.custom_minimum_size = Vector2(80, 8)
	bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hbox.add_child(bar)

# ── Search / filter ───────────────────────────────────────────────────────────
func _on_search_changed(text: String) -> void:
	var lower = text.to_lower()
	if lower == "":
		_filtered_ids = PokedexData.get_all_ids()
	else:
		_filtered_ids = PokedexData.get_catalogue().filter(func(e):
			return lower in e["name"].to_lower() or lower in e["type1"].to_lower() \
			       or lower in e.get("type2","").to_lower()
		).map(func(e): return e["id"])
	_build_grid()
	_update_count()

func _update_count() -> void:
	var seen := GameManager.seen_ids.size()
	var caught := GameManager.caught_ids.size()
	count_label.text = "Vistas: %d  Vinculadas: %d / %d" % [seen, caught, PokedexData.get_catalogue().size()]

func _load_creature_sprite(creature_id: String) -> Texture2D:
	var path := SPRITE_PATH + creature_id + "_base.png"
	return RuntimeTextureLoader.load_texture(path)

func _on_back_pressed() -> void:
	detail_view.hide()
	grid_view.show()

func _navigate(dir: int) -> void:
	var new_idx = clamp(_current_index + dir, 0, _filtered_ids.size() - 1)
	if new_idx == _current_index: return
	var seen = _filtered_ids[new_idx] in GameManager.seen_ids
	if seen:
		_open_detail(new_idx)
