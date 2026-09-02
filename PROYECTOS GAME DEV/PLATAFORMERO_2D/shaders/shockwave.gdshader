shader_type canvas_item;

// ============================================================
// shockwave.gdshader — Onda de choque 2D para pixel art
// ============================================================
// Uso: Aplica a un ColorRect que cubra toda la pantalla,
//      dentro de un CanvasLayer encima de todo el juego.
//      Usa BackBufferCopy (o hint_screen_texture) para
//      distorsionar lo que hay debajo.
//
// Ejemplo rápido:
//   var mat = material as ShaderMaterial
//   mat.set_shader_parameter("center", get_viewport().get_mouse_position() / get_viewport_rect().size)
//   mat.set_shader_parameter("force", 0.05)
//   # Anima "force" de 0.05 → 0.0 y "size" de 0.0 → 0.5
// ============================================================

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

// Centro de la onda en coordenadas UV (0.0 – 1.0)
uniform vec2 center = vec2(0.5, 0.5);

// Fuerza de la distorsión (0 = sin efecto)
uniform float force : hint_range(0.0, 0.1) = 0.0;

// Radio actual de la onda (animar de 0 → max)
uniform float size : hint_range(0.0, 1.5) = 0.0;

// Grosor del anillo de distorsión
uniform float thickness : hint_range(0.0, 0.3) = 0.1;

void fragment() {
    vec2 uv = SCREEN_UV;
    float dist = distance(uv, center);

    // Solo distorsiona dentro del anillo [size - thickness, size]
    if (dist >= size - thickness && dist <= size) {
        // Normalizar posición dentro del anillo (0 → 1)
        float diff = (dist - size + thickness) / thickness;
        // Curva suave tipo campana
        float wave = 1.0 - pow(abs(diff * 2.0 - 1.0), 2.0);
        // Desplazar UV radialmente
        vec2 dir = normalize(uv - center);
        uv -= dir * force * wave;
    }

    COLOR = texture(screen_texture, uv);
}
