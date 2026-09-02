## crt_scanline_controller.gd
## Controlador para el shader CRT Scanline.
##
## === SETUP ===
## 1. Crea un CanvasLayer (layer alto, ej. 100) en tu escena principal.
## 2. Agrega un ColorRect hijo que cubra toda la pantalla.
##    - Anchor: Full Rect  (Layout > Full Rect)
##    - Mouse Filter: Ignore  (para no bloquear clicks)
## 3. En el ColorRect, crea un ShaderMaterial con crt_scanline.gdshader.
## 4. Adjunta este script al ColorRect.
##
## === USO ===
## • Llama toggle_crt() para encender/apagar el efecto.
## • Llama set_intensity(val) con un valor 0.0–1.0 para ajustar las scanlines.
## • Llama pulse_crt(duration) para un flash retro momentáneo (ej. al entrar a una zona).
##
## Ejemplo desde otro nodo:
##   var crt = get_node("/root/Main/CRTLayer/CRTRect")
##   crt.toggle_crt()
##   crt.set_intensity(0.5)
##   crt.pulse_crt(0.8)

extends ColorRect

@export var default_scanline_strength: float = 0.35
@export var default_vignette_strength: float = 0.25
@export var default_curvature: float = 0.0

var _is_enabled: bool = true


func _ready() -> void:
	# Asegurar que el ColorRect cubra la pantalla
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE

	# Aplicar valores por defecto
	_set_param("scanline_strength", default_scanline_strength)
	_set_param("vignette_strength", default_vignette_strength)
	_set_param("curvature", default_curvature)
	_set_param("enabled", true)


## Enciende o apaga el efecto CRT
func toggle_crt() -> void:
	_is_enabled = !_is_enabled
	_set_param("enabled", _is_enabled)


## Ajusta la intensidad de las scanlines (0.0 = sin efecto, 1.0 = máximo)
func set_intensity(value: float) -> void:
	_set_param("scanline_strength", clamp(value, 0.0, 1.0))


## Ajusta la fuerza del viñeteado (0.0 = sin viñeta, 1.0 = viñeta fuerte)
func set_vignette(value: float) -> void:
	_set_param("vignette_strength", clamp(value, 0.0, 1.0))


## Ajusta la curvatura CRT (0.0 = plano, 0.05+ = curvado)
func set_curvature(value: float) -> void:
	_set_param("curvature", clamp(value, 0.0, 0.1))


## Flash retro momentáneo: sube intensidad y la regresa suavemente
func pulse_crt(duration: float = 0.5) -> void:
	var original := _get_param("scanline_strength")
	_set_param("scanline_strength", 0.9)
	_set_param("enabled", true)

	var tween := create_tween()
	tween.tween_method(
		func(val: float) -> void: _set_param("scanline_strength", val),
		0.9, original, duration
	)
	tween.tween_callback(func() -> void:
		_set_param("enabled", _is_enabled)  # Restaurar estado previo
	)


# --- Helpers internos ---

func _set_param(param_name: String, value: Variant) -> void:
	if material and material is ShaderMaterial:
		(material as ShaderMaterial).set_shader_parameter(param_name, value)


func _get_param(param_name: String) -> Variant:
	if material and material is ShaderMaterial:
		return (material as ShaderMaterial).get_shader_parameter(param_name)
	return null
