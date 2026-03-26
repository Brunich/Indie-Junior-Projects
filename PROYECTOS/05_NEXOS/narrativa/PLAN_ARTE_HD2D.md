# EMBERVEIL — Plan de Arte HD-2D
> Hoja de ruta para pasar de pixel art placeholder a arte HD-2D de calidad.
> Incluye herramientas, workflow paso a paso, y lo que Bruno hace vs lo que se automatiza.

---

## Por qué HD-2D y no pixel art mejorado

El pixel art tiene un techo real en 2026. Para un juego de portafolio que compita visualmente:
- Pixel art requiere artistas especializados para verse profesional
- HD-2D (estilo Octopath Traveler) se ve premium con sprites 2D + iluminación moderna
- La IA puede generar arte HD-2D consistente — pixel art consistente con IA es mucho más difícil

**Referencia visual objetivo:** Cassette Beasts + Sea of Stars (sprites detallados, fondos con profundidad)

---

## El Stack de Herramientas

### 1. Scenario.gg — Generación de sprites
**URL:** https://scenario.gg
**Costo:** Plan gratuito disponible (limitado), ~$15/mes para producción

**Por qué es el mejor para este proyecto:**
- Diseñado específicamente para game assets
- Permite entrenar un modelo con tu propio estilo (Fine-tuning)
- Genera sprites con fondo transparente directamente
- Consistencia visual entre personajes del mismo juego
- Exporta PNG listos para importar en Godot

**Alternativa gratuita:** ComfyUI con modelo anime/RPG (ya instalado en tu PC)

### 2. Spine 2D — Animación esquelética
**URL:** https://esotericsoftware.com
**Costo:** ~$70 licencia perpetua Essential / $300 Professional

**Por qué Spine en vez de animación frame-by-frame:**
- Dibujas el personaje UNA vez, lo animas moviendo "huesos"
- 1 sprite bien hecho → 50+ animaciones (caminar, correr, atacar, dañado, morir, idle)
- Godot 4 tiene soporte nativo para Spine a través de plugin oficial
- Los archivos Spine (.json + atlas) se importan directamente al proyecto

**Alternativa gratuita:** DragonBones (menos features, funciona en Godot con plugin)

### 3. Godot 4 — Motor (ya en uso ✓)
El plugin de Spine para Godot 4: https://github.com/EsotericSoftware/spine-runtimes

---

## Workflow Completo: De Concepto a Sprite Animado

### FASE 1 — Definir el estilo (Bruno hace esto una vez)
**Tiempo:** 2-3 horas

1. En Scenario.gg, crear un proyecto nuevo: "Emberveil Creatures"
2. Subir 5-10 imágenes de referencia de criaturas que tengan el estilo que quieres
   - Búscalas en ArtStation con "RPG creature concept art" o "monster design indie game"
   - O usa los sprites actuales mejorados como base
3. Hacer Fine-tuning del modelo con esas referencias
4. El modelo aprende el estilo y lo replica para nuevas criaturas

### FASE 2 — Generar sprites de Tonales (automatizado)
**Tiempo:** 30 min para las 19 criaturas Emberveil

**Prompt base para Scenario.gg:**
```
[nombre del Tonal], [tipo de criatura], fantasy RPG creature,
2D game sprite, detailed illustration, clean lineart,
transparent background, front view, full body,
vibrant colors, Mesoamerican inspired design elements,
no background, game asset ready
```

**Variaciones para cada Tonal:**
- Frente (batalla)
- Espalda (batalla desde atrás)
- Icono pequeño (para UI del Códice)

### FASE 3 — Preparar para animación en Spine
**Tiempo:** 1-2 horas por criatura

1. Abrir el sprite en Photoshop/Krita/Gimp
2. Separar en capas: cuerpo, cabeza, extremidades, cola, efectos
3. Importar a Spine como "skeleton"
4. Crear set de animaciones base:
   - `idle` — respiración/movimiento suave
   - `walk` — caminar en overworld
   - `battle_enter` — entrada a batalla
   - `attack` — animación de ataque genérico
   - `hurt` — recibir daño
   - `faint` — desmayarse

### FASE 4 — Integrar en Godot 4
**Tiempo:** 30 min por criatura

1. Exportar Spine como `.json` + atlas PNG
2. Instalar plugin de Spine en Godot: `addons/spine_godot`
3. Crear nodo `SpineSprite` en las escenas de batalla y overworld
4. Conectar señales de animación con los eventos del juego

---

## Lo que Bruno hace vs lo que se automatiza

### Bruno hace (decisiones creativas):
- Elegir referencias de estilo en Scenario.gg (una vez)
- Aprobar o rechazar sprites generados
- Ajustar proporciones en Spine si algo no se ve bien
- Definir qué animaciones necesita cada criatura

### Se automatiza:
- Generación masiva de sprites (Scenario.gg API o manual en batch)
- Consistencia de estilo entre criaturas (el modelo entrenado lo mantiene)
- Export de animaciones desde Spine
- Import en Godot (una vez configurado el pipeline)

### Claude Code hace:
- Integrar el plugin de Spine en Godot
- Conectar las animaciones con el sistema de batalla
- Reemplazar los sprites placeholder con los nuevos

---

## Plan de Implementación por Semanas

### Semana 1 — Setup (Bruno)
- [ ] Crear cuenta en Scenario.gg
- [ ] Recopilar 5-10 referencias de estilo (ArtStation, Pinterest)
- [ ] Hacer Fine-tuning del modelo con las referencias
- [ ] Generar sprites de los 3 primeros Tonales (Embral, Embralcinder, Folimp)
- [ ] Evaluar calidad y ajustar el modelo si es necesario

### Semana 2 — Producción de sprites
- [ ] Generar las 19 criaturas Emberveil con Scenario.gg
- [ ] Revisar y aprobar cada sprite
- [ ] Exportar con fondo transparente

### Semana 3 — Animación
- [ ] Comprar/probar Spine (hay versión de prueba)
- [ ] Animar Embral como prueba de concepto
- [ ] Establecer el pipeline Spine → Godot
- [ ] Si funciona, animar las 19 criaturas (o priorizar las más visibles)

### Semana 4 — Integración
- [ ] Claude Code integra Spine en Godot
- [ ] Reemplazar sprites de batalla y overworld
- [ ] Test visual completo

---

## Alternativa más rápida si no hay presupuesto para Spine

Usar **Godot's AnimatedSprite2D** con sprites generados por Scenario.gg:
- Genera 4-6 frames por animación directamente en Scenario.gg
- Importa como AnimatedSprite2D en Godot
- Más limitado que Spine, pero funciona sin costo extra
- Para un portafolio, esto es suficiente

---

## Sobre los Mapas (Automatización con LDtk)

Investigación completada. El workflow recomendado para reemplazar Spritefusion:

### Stack recomendado:
1. **LDtk** (gratuito) — editor de niveles con autotiling
   - Descarga: https://deepnight.itch.io/ldtk
   - Más rápido que Spritefusion para mapas grandes
   - Plugin de Godot: https://godotengine.org/asset-library/asset/2181

2. **Wave Function Collapse** — generación procedural de base
   - Plugin de Godot: https://godotengine.org/asset-library/asset/1951
   - Genera el esqueleto del mapa automáticamente
   - LDtk lo refina a mano

### Workflow de mapas (20 min por mapa vs 2+ horas en Spritefusion):
1. Configurar WFC con un mapa "ejemplo" de tu estilo (una vez)
2. WFC genera la estructura base del mapa en 30 segundos
3. Abrir en LDtk, ajustar detalles con autotiling
4. Importar a Godot con el plugin LDtk
5. Refinar en Godot si es necesario

**Reducción de tiempo estimada: 70%** vs método actual con Spritefusion.

---

*Plan creado: Cowork marzo 2026*
*Revisión sugerida cuando se complete la Semana 1*
