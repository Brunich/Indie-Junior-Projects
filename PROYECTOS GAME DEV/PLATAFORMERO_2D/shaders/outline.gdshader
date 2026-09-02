// outline.gdshader — Outline de 1px para sprites pixel art
// Uso: ShaderMaterial en Sprite2D del personaje/enemigo
// Activar: material.set_shader_parameter("show_outline", true)
shader_type canvas_item;

uniform bool show_outline = true;
uniform vec4 outline_color: source_color = vec4(0.0, 0.0, 0.0, 1.0);
uniform float outline_width: hint_range(0.5, 3.0, 0.5) = 1.0;

void fragment() {
    vec2 size = TEXTURE_PIXEL_SIZE * outline_width;
    vec4 col = texture(TEXTURE, UV);
    
    if (show_outline && col.a < 0.5) {
        // Samplear los 4 vecinos para detectar borde
        float left  = texture(TEXTURE, UV + vec2(-size.x, 0.0)).a;
        float right = texture(TEXTURE, UV + vec2( size.x, 0.0)).a;
        float up    = texture(TEXTURE, UV + vec2(0.0, -size.y)).a;
        float down  = texture(TEXTURE, UV + vec2(0.0,  size.y)).a;
        
        float neighbor = max(max(left, right), max(up, down));
        if (neighbor > 0.5) {
            COLOR = outline_color;
            return;
        }
    }
    COLOR = col;
}
