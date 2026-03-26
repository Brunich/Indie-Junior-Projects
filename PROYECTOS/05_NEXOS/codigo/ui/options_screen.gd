## OptionsScreen — Game settings UI
## Built programmatically with TabContainer (CLASSIC | EXTRAS)
## Updates GameOptions singleton in real-time
extends Control

@onready var game_options = GameOptions

var tab_container: TabContainer
var classic_container: VBoxContainer
var extras_container: VBoxContainer

# Classic controls
var text_speed_option: OptionButton
var battle_animations_check: CheckButton
var battle_style_option: OptionButton
var sound_option: OptionButton
var bgm_volume_slider: HSlider
var sfx_volume_slider: HSlider

# Extras controls
var exp_share_auto_check: CheckButton
var run_anywhere_check: CheckButton
var show_damage_nums_check: CheckButton
var show_type_hint_check: CheckButton
var show_move_pp_check: CheckButton
var auto_heal_box_check: CheckButton
var nuzlocke_mode_check: CheckButton
var hardcore_mode_check: CheckButton
var language_option: OptionButton

func _ready() -> void:
	setup_ui()
	load_values()
	connect_signals()

func setup_ui() -> void:
	var main_panel = Panel.new()
	main_panel.add_theme_stylebox_override("panel", get_theme_stylebox("panel", "Panel"))
	add_child(main_panel)
	main_panel.set_anchors_preset(Control.PRESET_CENTER)
	main_panel.custom_minimum_size = Vector2(600, 500)

	var main_vbox = VBoxContainer.new()
	main_panel.add_child(main_vbox)
	main_vbox.set_anchors_preset(Control.PRESET_FULL_RECT)
	main_vbox.add_theme_constant_override("separation", 8)

	# Title
	var title = Label.new()
title.text = "AJUSTES"
	title.add_theme_font_size_override("font_size", 24)
	main_vbox.add_child(title)

	# TabContainer
	tab_container = TabContainer.new()
	main_vbox.add_child(tab_container)
	tab_container.custom_minimum_size = Vector2(580, 400)
	tab_container.size_flags_vertical = Control.SIZE_EXPAND_FILL

	# ── CLASSIC TAB ───────────────────────────────────────────────────────────
	classic_container = VBoxContainer.new()
	classic_container.add_theme_constant_override("separation", 6)
	tab_container.add_child(classic_container)
	tab_container.set_tab_title(0, "CLASSIC")

	# Text Speed
	var text_speed_hbox = HBoxContainer.new()
	classic_container.add_child(text_speed_hbox)
	var text_speed_label = Label.new()
text_speed_label.text = "Velocidad de texto"
	text_speed_label.custom_minimum_size = Vector2(150, 0)
	text_speed_hbox.add_child(text_speed_label)
	text_speed_option = OptionButton.new()
text_speed_option.add_item("Lenta", 0)
text_speed_option.add_item("Media", 1)
text_speed_option.add_item("Rapida", 2)
text_speed_option.add_item("Instantanea", 3)
	text_speed_hbox.add_child(text_speed_option)

	# Battle Animations
	battle_animations_check = CheckButton.new()
battle_animations_check.text = "Animaciones de combate"
	classic_container.add_child(battle_animations_check)

	# Battle Style
	var battle_style_hbox = HBoxContainer.new()
	classic_container.add_child(battle_style_hbox)
	var battle_style_label = Label.new()
battle_style_label.text = "Estilo de combate"
	battle_style_label.custom_minimum_size = Vector2(150, 0)
	battle_style_hbox.add_child(battle_style_label)
	battle_style_option = OptionButton.new()
battle_style_option.add_item("Cambio", 0)
battle_style_option.add_item("Fijo", 1)
	battle_style_hbox.add_child(battle_style_option)

	# Sound
	var sound_hbox = HBoxContainer.new()
	classic_container.add_child(sound_hbox)
	var sound_label = Label.new()
sound_label.text = "Audio"
	sound_label.custom_minimum_size = Vector2(150, 0)
	sound_hbox.add_child(sound_label)
	sound_option = OptionButton.new()
	sound_option.add_item("Mono", 0)
	sound_option.add_item("Stereo", 1)
	sound_hbox.add_child(sound_option)

	# BGM Volume
	var bgm_hbox = HBoxContainer.new()
	classic_container.add_child(bgm_hbox)
	var bgm_label = Label.new()
bgm_label.text = "Volumen BGM"
	bgm_label.custom_minimum_size = Vector2(150, 0)
	bgm_hbox.add_child(bgm_label)
	bgm_volume_slider = HSlider.new()
	bgm_volume_slider.min_value = 0.0
	bgm_volume_slider.max_value = 1.0
	bgm_volume_slider.step = 0.05
	bgm_hbox.add_child(bgm_volume_slider)
	var bgm_value_label = Label.new()
	bgm_value_label.text = "0.8"
	bgm_value_label.custom_minimum_size = Vector2(40, 0)
	bgm_hbox.add_child(bgm_value_label)
	bgm_volume_slider.value_changed.connect(func(val): bgm_value_label.text = "%.1f" % val)

	# SFX Volume
	var sfx_hbox = HBoxContainer.new()
	classic_container.add_child(sfx_hbox)
	var sfx_label = Label.new()
sfx_label.text = "Volumen SFX"
	sfx_label.custom_minimum_size = Vector2(150, 0)
	sfx_hbox.add_child(sfx_label)
	sfx_volume_slider = HSlider.new()
	sfx_volume_slider.min_value = 0.0
	sfx_volume_slider.max_value = 1.0
	sfx_volume_slider.step = 0.05
	sfx_hbox.add_child(sfx_volume_slider)
	var sfx_value_label = Label.new()
	sfx_value_label.text = "1.0"
	sfx_value_label.custom_minimum_size = Vector2(40, 0)
	sfx_hbox.add_child(sfx_value_label)
	sfx_volume_slider.value_changed.connect(func(val): sfx_value_label.text = "%.1f" % val)

	# ── EXTRAS TAB ────────────────────────────────────────────────────────────
	extras_container = VBoxContainer.new()
	extras_container.add_theme_constant_override("separation", 6)
	tab_container.add_child(extras_container)
	tab_container.set_tab_title(1, "EXTRAS")

	exp_share_auto_check = CheckButton.new()
exp_share_auto_check.text = "EXP compartida auto"
	extras_container.add_child(exp_share_auto_check)

	run_anywhere_check = CheckButton.new()
run_anywhere_check.text = "Huir en cualquier lado"
	extras_container.add_child(run_anywhere_check)

	show_damage_nums_check = CheckButton.new()
show_damage_nums_check.text = "Ver numeros de dano"
	extras_container.add_child(show_damage_nums_check)

	show_type_hint_check = CheckButton.new()
show_type_hint_check.text = "Ver pista de tipos"
	extras_container.add_child(show_type_hint_check)

	show_move_pp_check = CheckButton.new()
show_move_pp_check.text = "Ver PP de tecnicas"
	extras_container.add_child(show_move_pp_check)

	auto_heal_box_check = CheckButton.new()
auto_heal_box_check.text = "Curado auto al guardar"
	extras_container.add_child(auto_heal_box_check)

	nuzlocke_mode_check = CheckButton.new()
nuzlocke_mode_check.text = "Modo reto"
	extras_container.add_child(nuzlocke_mode_check)

	hardcore_mode_check = CheckButton.new()
hardcore_mode_check.text = "Modo duro"
	extras_container.add_child(hardcore_mode_check)

	# Language
	var language_hbox = HBoxContainer.new()
	extras_container.add_child(language_hbox)
	var language_label = Label.new()
language_label.text = "Idioma"
	language_label.custom_minimum_size = Vector2(150, 0)
	language_hbox.add_child(language_label)
	language_option = OptionButton.new()
	language_option.add_item("Español", 0)
language_option.add_item("Ingles", 1)
	language_hbox.add_child(language_option)

	# ── BUTTONS ───────────────────────────────────────────────────────────────
	var button_hbox = HBoxContainer.new()
	main_vbox.add_child(button_hbox)
	button_hbox.add_theme_constant_override("separation", 10)

	var save_btn = Button.new()
save_btn.text = "GUARDAR"
	button_hbox.add_child(save_btn)
	save_btn.pressed.connect(save_settings)

	var cancel_btn = Button.new()
cancel_btn.text = "CANCELAR"
	button_hbox.add_child(cancel_btn)
	cancel_btn.pressed.connect(queue_free)

func connect_signals() -> void:
	text_speed_option.item_selected.connect(func(idx): game_options.text_speed = idx)
	battle_animations_check.toggled.connect(func(val): game_options.battle_animations = val)
	battle_style_option.item_selected.connect(func(idx): game_options.battle_style = idx)
	sound_option.item_selected.connect(func(idx): game_options.sound = idx)
	bgm_volume_slider.value_changed.connect(func(val): game_options.bgm_volume = val)
	sfx_volume_slider.value_changed.connect(func(val): game_options.sfx_volume = val)

	exp_share_auto_check.toggled.connect(func(val): game_options.exp_share_auto = val)
	run_anywhere_check.toggled.connect(func(val): game_options.run_anywhere = val)
	show_damage_nums_check.toggled.connect(func(val): game_options.show_damage_nums = val)
	show_type_hint_check.toggled.connect(func(val): game_options.show_type_hint = val)
	show_move_pp_check.toggled.connect(func(val): game_options.show_move_pp = val)
	auto_heal_box_check.toggled.connect(func(val): game_options.auto_heal_box = val)
	nuzlocke_mode_check.toggled.connect(func(val): game_options.nuzlocke_mode = val)
	hardcore_mode_check.toggled.connect(func(val): game_options.hardcore_mode = val)
	language_option.item_selected.connect(func(idx): game_options.language = "es" if idx == 0 else "en")

func load_values() -> void:
	text_speed_option.select(game_options.text_speed)
	battle_animations_check.button_pressed = game_options.battle_animations
	battle_style_option.select(game_options.battle_style)
	sound_option.select(game_options.sound)
	bgm_volume_slider.value = game_options.bgm_volume
	sfx_volume_slider.value = game_options.sfx_volume

	exp_share_auto_check.button_pressed = game_options.exp_share_auto
	run_anywhere_check.button_pressed = game_options.run_anywhere
	show_damage_nums_check.button_pressed = game_options.show_damage_nums
	show_type_hint_check.button_pressed = game_options.show_type_hint
	show_move_pp_check.button_pressed = game_options.show_move_pp
	auto_heal_box_check.button_pressed = game_options.auto_heal_box
	nuzlocke_mode_check.button_pressed = game_options.nuzlocke_mode
	hardcore_mode_check.button_pressed = game_options.hardcore_mode
	language_option.select(0 if game_options.language == "es" else 1)

func save_settings() -> void:
	game_options.save_options()
	queue_free()
