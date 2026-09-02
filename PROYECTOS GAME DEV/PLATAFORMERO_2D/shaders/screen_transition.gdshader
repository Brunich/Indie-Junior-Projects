// screen_transition.gdshader — Transición de pantalla con wipe circular
// Uso: aplicar a un ColorRect de pantalla completa en CanvasLayer
// Animar "progress" de 0.0 → 1.0 para fade out, 1.0 → 0.0 para fade in
shader_type canvas_item;

uniform float progress: hint_range(0.0, 1.0) = 0.0;
uniform vec4 transition_color: source_color = vec4(0.0, 0.0, 0.0, 1.0);

void fragment() {
    // Wipe circular desde el centro
    vec2 center = vec2(0.5, 0.5);
    float dist = distance(UV, center) * 1.5;
    float alpha = step(progress, dist);
    COLOR = vec4(transition_color.rgb, alpha);
}
