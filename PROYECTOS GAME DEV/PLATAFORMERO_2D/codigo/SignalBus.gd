## SignalBus.gd
## Autoload global de señales - Desacopla todos los sistemas
## Todos los sistemas emiten aquí, todos escuchan aquí

extends Node

# ===== JUGADOR =====
signal player_died(player_id: int)
signal player_respawned(player_id: int, position: Vector2)
signal player_hit_checkpoint(player_id: int, checkpoint_id: String)
signal player_collected_coin(player_id: int)
signal player_used_powerup(player_id: int, type: String)
signal player_first_input(player_id: int)
signal player_shot(player_id: int, position: Vector2)
signal player_landed(player_id: int)
signal player_jumped(player_id: int)
signal player_took_damage(player_id: int, amount: int)

# ===== ENEMIGOS =====
signal enemy_died(enemy_id: int, position: Vector2)
signal enemy_spawned(enemy_id: int, position: Vector2)
signal enemy_took_damage(enemy_id: int, amount: int)
signal boss_phase_changed(boss_id: String, phase: int)
signal boss_died(boss_id: String)

# ===== NIVEL =====
signal level_started(level_name: String)
signal level_completed(level_name: String, time_seconds: float)
signal level_transition_requested(target_scene: String)
signal level_paused(paused: bool)

# ===== BEAT / AUDIO =====
signal beat_triggered(beat_index: int)
signal on_beat_kill(player_id: int)
signal combo_updated(player_id: int, combo: int)
signal music_changed(track_name: String)

# ===== DIÁLOGO =====
signal dialogue_started(trigger_id: String)
signal dialogue_ended(trigger_id: String)

# ===== LOGROS =====
signal achievement_trigger(trigger_id: String, context: Dictionary)

# ===== UI =====
signal hud_updated(type: String, value)
signal menu_opened(menu_name: String)
signal menu_closed(menu_name: String)

# ===== JUEGO =====
signal game_paused
signal game_resumed
signal game_over(reason: String)
signal game_won

# ===== CO-OP =====
signal players_synchronized(player_ids: Array)
signal coop_disconnect(player_id: int)

func _ready() -> void:
    print("✅ SignalBus inicializado - Todas las señales listas")
