# 01 — Pong

Pong clásico en **Godot 4.2+**. Primer proyecto del portfolio junior: física simple, colisiones y puntuación.

## Controles

| Jugador | Movimiento |
|---------|------------|
| J1 | W / S |
| J2 / CPU | Flechas arriba / abajo |
| Reiniciar | R o Enter |

La raqueta derecha usa IA básica (sigue la pelota). Cambia `control_scheme` a `p2` en el Inspector para 2 jugadores humanos.

## Cómo abrir

1. Godot 4.2+ → Import → `project.godot`
2. Play (F5)

## Estructura

```
01_PONG/
  scenes/main.tscn
  codigo/
    game.gd      # Marcador y reinicio
    paddle.gd    # Raquetas (humano o CPU)
    ball.gd      # Rebotes y goles
```

## Aprendizajes

- `CharacterBody2D` + `move_and_collide`
- Grupos (`paddle`, `wall`, `goal`, `ball`)
- Señales entre nodos
- Input map personalizado

Autor: Bruno Salas Rodriguez · UANL
