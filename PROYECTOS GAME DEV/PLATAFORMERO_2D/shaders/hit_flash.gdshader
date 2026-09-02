// hit_flash.gdshader — Parpadeo blanco al recibir daño
// Uso: asignar como ShaderMaterial en el Sprite2D del player/enemigo
// Activar: material.set_shader_parameter("flash", true)

shader_type canvas_item;

uniform bool flash = false;
uniform vec4 flash_color: source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float flash_intensity: hint_range(0.0, 1.0) = 1.0;

void fragment() {
    vec4 original = texture(TEXTURE, UV);

    if (flash && original.a > 0.0) {
        // Mezcla entre color original y flash_color
        COLOR = mix(original, vec4(flash_color.rgb, original.a), flash_intensity);
    } else {
        COLOR = original;
    }
}
