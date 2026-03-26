#!/usr/bin/env python3
"""Descarga datos de Gen 1 Pokémon desde PokeAPI y sprites desde GitHub"""
import json
import urllib.request
import os
import time

POKE_DIR = "/sessions/eager-funny-fermat/mnt/IA TEAM/PROYECTOS/05_POKEMON"
DATA_DIR = f"{POKE_DIR}/datos"
SPRITE_DIR = f"{POKE_DIR}/sprites/pokemon"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SPRITE_DIR, exist_ok=True)

# Tabla de tipos Gen 1 (se construye localmente, sin API calls innecesarios)
TYPE_CHART = {
    "normal":   {"rock": 0.5, "ghost": 0, "steel": 0.5},
    "fire":     {"fire": 0.5, "water": 0.5, "grass": 2, "ice": 2, "bug": 2, "rock": 0.5, "dragon": 0.5, "steel": 2},
    "water":    {"fire": 2, "water": 0.5, "grass": 0.5, "ground": 2, "rock": 2, "dragon": 0.5},
    "electric": {"water": 2, "electric": 0.5, "grass": 0.5, "ground": 0, "flying": 2, "dragon": 0.5},
    "grass":    {"fire": 0.5, "water": 2, "grass": 0.5, "poison": 0.5, "ground": 2, "flying": 0.5, "bug": 0.5, "rock": 2, "dragon": 0.5, "steel": 0.5},
    "ice":      {"water": 0.5, "grass": 2, "ice": 0.5, "ground": 2, "flying": 2, "dragon": 2, "steel": 0.5},
    "fighting": {"normal": 2, "ice": 2, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2, "ghost": 0, "dark": 2, "steel": 2, "fairy": 0.5},
    "poison":   {"grass": 2, "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5, "steel": 0, "fairy": 2},
    "ground":   {"fire": 2, "electric": 2, "grass": 0.5, "poison": 2, "flying": 0, "bug": 0.5, "rock": 2, "steel": 2},
    "flying":   {"electric": 0.5, "grass": 2, "fighting": 2, "bug": 2, "rock": 0.5, "steel": 0.5},
    "psychic":  {"fighting": 2, "poison": 2, "psychic": 0.5, "dark": 0, "steel": 0.5},
    "bug":      {"fire": 0.5, "grass": 2, "fighting": 0.5, "flying": 0.5, "psychic": 2, "ghost": 0.5, "dark": 2, "steel": 0.5, "fairy": 0.5},
    "rock":     {"fire": 2, "ice": 2, "fighting": 0.5, "ground": 0.5, "flying": 2, "bug": 2, "steel": 0.5},
    "ghost":    {"normal": 0, "psychic": 2, "ghost": 2, "dark": 0.5},
    "dragon":   {"dragon": 2, "steel": 0.5, "fairy": 0},
    "dark":     {"fighting": 0.5, "psychic": 2, "ghost": 2, "dark": 0.5, "fairy": 0.5},
    "steel":    {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2, "rock": 2, "steel": 0.5, "fairy": 2},
    "fairy":    {"fire": 0.5, "fighting": 2, "poison": 0.5, "dragon": 2, "dark": 2, "steel": 0.5},
}

# Datos base Gen 1 — hardcodeados para no depender de API calls masivos
# Stats: hp, atk, def, sp_atk, sp_def, spd
POKEMON_GEN1 = [
    (1, "Bulbasaur", ["grass", "poison"], [45, 49, 49, 65, 65, 45], 64, 1, 45, [33, 36, 45]),
    (2, "Ivysaur", ["grass", "poison"], [60, 62, 63, 80, 80, 60], 142, 2, 45, [45, 0, 0]),
    (3, "Venusaur", ["grass", "poison"], [80, 82, 83, 100, 100, 80], 236, 3, 45, [0, 0, 0]),
    (4, "Charmander", ["fire"], [39, 52, 43, 60, 50, 65], 62, 4, 45, [16, 36, 0]),
    (5, "Charmeleon", ["fire"], [58, 64, 58, 80, 65, 80], 142, 5, 45, [36, 0, 0]),
    (6, "Charizard", ["fire", "flying"], [78, 84, 78, 109, 85, 100], 240, 6, 45, [0, 0, 0]),
    (7, "Squirtle", ["water"], [44, 48, 65, 50, 64, 43], 63, 7, 45, [16, 36, 0]),
    (8, "Wartortle", ["water"], [59, 63, 80, 65, 80, 58], 142, 8, 45, [36, 0, 0]),
    (9, "Blastoise", ["water"], [79, 83, 100, 85, 105, 78], 239, 9, 45, [0, 0, 0]),
    (10, "Caterpie", ["bug"], [45, 30, 35, 20, 20, 45], 53, 11, 255, [7, 0, 0]),
    (11, "Metapod", ["bug"], [50, 20, 55, 25, 25, 30], 72, 12, 120, [10, 0, 0]),
    (12, "Butterfree", ["bug", "flying"], [60, 45, 50, 90, 80, 70], 160, 0, 45, [0, 0, 0]),
    (13, "Weedle", ["bug", "poison"], [40, 35, 30, 20, 20, 50], 52, 14, 255, [7, 0, 0]),
    (14, "Kakuna", ["bug", "poison"], [45, 25, 50, 25, 25, 35], 72, 15, 120, [10, 0, 0]),
    (15, "Beedrill", ["bug", "poison"], [65, 90, 40, 45, 80, 75], 159, 0, 45, [0, 0, 0]),
    (16, "Pidgey", ["normal", "flying"], [40, 45, 40, 35, 35, 56], 55, 17, 255, [18, 36, 0]),
    (17, "Pidgeotto", ["normal", "flying"], [63, 60, 55, 50, 50, 71], 113, 18, 120, [36, 0, 0]),
    (18, "Pidgeot", ["normal", "flying"], [83, 80, 75, 70, 70, 101], 216, 0, 45, [0, 0, 0]),
    (19, "Rattata", ["normal"], [30, 56, 35, 25, 35, 72], 57, 20, 255, [20, 0, 0]),
    (20, "Raticate", ["normal"], [55, 81, 60, 50, 70, 97], 116, 0, 127, [0, 0, 0]),
    (25, "Pikachu", ["electric"], [35, 55, 40, 50, 50, 90], 112, 26, 190, [0, 0, 0]),
    (26, "Raichu", ["electric"], [60, 90, 55, 90, 80, 110], 218, 0, 75, [0, 0, 0]),
    (39, "Jigglypuff", ["normal", "fairy"], [115, 45, 20, 45, 25, 20], 76, 40, 170, [0, 0, 0]),
    (52, "Meowth", ["normal"], [40, 45, 35, 40, 40, 90], 69, 53, 255, [28, 0, 0]),
    (54, "Psyduck", ["water"], [50, 52, 48, 65, 50, 55], 80, 55, 190, [33, 0, 0]),
    (63, "Abra", ["psychic"], [25, 20, 15, 105, 55, 90], 73, 64, 200, [16, 36, 0]),
    (66, "Machop", ["fighting"], [70, 80, 50, 35, 35, 35], 75, 67, 180, [28, 36, 0]),
    (74, "Geodude", ["rock", "ground"], [40, 80, 100, 30, 30, 20], 73, 75, 255, [25, 36, 0]),
    (94, "Gengar", ["ghost", "poison"], [60, 65, 60, 130, 75, 110], 225, 0, 45, [0, 0, 0]),
    (129, "Magikarp", ["water"], [20, 10, 55, 15, 20, 80], 40, 130, 255, [20, 0, 0]),
    (130, "Gyarados", ["water", "flying"], [95, 125, 79, 60, 100, 81], 214, 0, 45, [0, 0, 0]),
    (133, "Eevee", ["normal"], [55, 55, 50, 45, 65, 55], 92, 0, 45, [0, 0, 0]),
    (143, "Snorlax", ["normal"], [160, 110, 65, 65, 110, 30], 154, 0, 25, [0, 0, 0]),
    (147, "Dratini", ["dragon"], [41, 64, 45, 50, 50, 50], 67, 148, 45, [30, 55, 0]),
    (148, "Dragonair", ["dragon"], [61, 84, 65, 70, 70, 70], 144, 149, 45, [55, 0, 0]),
    (149, "Dragonite", ["dragon", "flying"], [91, 134, 95, 100, 100, 80], 270, 0, 45, [0, 0, 0]),
    (150, "Mewtwo", ["psychic"], [106, 110, 90, 154, 90, 130], 306, 0, 3, [0, 0, 0]),
    (151, "Mew", ["psychic"], [100, 100, 100, 100, 100, 100], 270, 0, 45, [0, 0, 0]),
]
# Formato: (id, nombre, tipos, [hp,atk,def,sp_atk,sp_def,spd], exp_base, evoluciona_a, catch_rate, [niveles_evolucion])

# Movimientos Gen 1 más importantes
MOVES = {
    "tackle":     {"power": 40, "type": "normal", "category": "physical", "pp": 35, "accuracy": 100},
    "growl":      {"power": 0,  "type": "normal", "category": "status",   "pp": 40, "accuracy": 100, "effect": "lower_atk"},
    "vine_whip":  {"power": 45, "type": "grass",  "category": "special",  "pp": 25, "accuracy": 100},
    "ember":      {"power": 40, "type": "fire",   "category": "special",  "pp": 25, "accuracy": 100, "effect": "burn_10"},
    "scratch":    {"power": 40, "type": "normal", "category": "physical", "pp": 35, "accuracy": 100},
    "water_gun":  {"power": 40, "type": "water",  "category": "special",  "pp": 25, "accuracy": 100},
    "thundershock":{"power": 40,"type": "electric","category": "special", "pp": 30, "accuracy": 100, "effect": "paralyze_10"},
    "quick_attack":{"power": 40,"type": "normal", "category": "physical", "pp": 30, "accuracy": 100, "priority": 1},
    "bite":       {"power": 60, "type": "dark",   "category": "physical", "pp": 25, "accuracy": 100, "effect": "flinch_30"},
    "psychic_move":{"power": 90,"type": "psychic","category": "special",  "pp": 10, "accuracy": 100, "effect": "lower_sp_def_10"},
    "surf":       {"power": 90, "type": "water",  "category": "special",  "pp": 15, "accuracy": 100},
    "flamethrower":{"power": 90,"type": "fire",   "category": "special",  "pp": 15, "accuracy": 100, "effect": "burn_10"},
    "thunderbolt":{"power": 90, "type": "electric","category": "special", "pp": 15, "accuracy": 100, "effect": "paralyze_10"},
    "ice_beam":   {"power": 90, "type": "ice",    "category": "special",  "pp": 10, "accuracy": 100, "effect": "freeze_10"},
    "hyper_beam": {"power": 150,"type": "normal", "category": "special",  "pp": 5,  "accuracy": 90,  "effect": "recharge"},
    "earthquake": {"power": 100,"type": "ground", "category": "physical", "pp": 10, "accuracy": 100},
    "dragon_rage": {"power": 40,"type": "dragon", "category": "special",  "pp": 10, "accuracy": 100},
    "splash":     {"power": 0,  "type": "normal", "category": "status",   "pp": 40, "accuracy": 100, "effect": "nothing"},
    "swords_dance":{"power": 0, "type": "normal", "category": "status",   "pp": 30, "accuracy": 100, "effect": "raise_atk_2"},
    "string_shot":{"power": 0,  "type": "bug",    "category": "status",   "pp": 40, "accuracy": 95,  "effect": "lower_spd"},
    "poison_sting":{"power": 15,"type": "poison", "category": "physical", "pp": 35, "accuracy": 100, "effect": "poison_30"},
    "recover":    {"power": 0,  "type": "normal", "category": "status",   "pp": 10, "accuracy": 100, "effect": "heal_half"},
    "amnesia":    {"power": 0,  "type": "psychic","category": "status",   "pp": 20, "accuracy": 100, "effect": "raise_sp_atk_2"},
    "transform":  {"power": 0,  "type": "normal", "category": "status",   "pp": 10, "accuracy": 100, "effect": "transform"},
}

# Moveset por nivel para starters y algunos básicos
LEVELUP_MOVES = {
    1:  [(1, "tackle"), (1, "growl"), (7, "vine_whip"), (13, "poison_sting"), (22, "razor_leaf"), (30, "sleep_powder")],
    4:  [(1, "scratch"), (1, "growl"), (9, "ember"), (15, "smokescreen"), (22, "fire_spin"), (31, "slash")],
    7:  [(1, "tackle"), (1, "tail_whip"), (7, "water_gun"), (13, "bite"), (22, "rapid_spin"), (28, "protect")],
    25: [(1, "thundershock"), (1, "growl"), (9, "quick_attack"), (16, "thunderwave"), (26, "thunderbolt"), (33, "agility")],
    94: [(1, "hypnosis"), (1, "lick"), (29, "night_shade"), (38, "mean_look"), (46, "dream_eater"), (54, "destiny_bond")],
}

# Guardar datos como JSON
pokemon_data = {}
for entry in POKEMON_GEN1:
    pid, name, types, stats, exp_base, evolves_to, catch_rate, evo_levels = entry
    pokemon_data[str(pid)] = {
        "id": pid,
        "name": name,
        "name_es": name,
        "types": types,
        "base_stats": {
            "hp": stats[0], "attack": stats[1], "defense": stats[2],
            "sp_attack": stats[3], "sp_defense": stats[4], "speed": stats[5]
        },
        "base_exp": exp_base,
        "evolves_to": evolves_to,
        "catch_rate": catch_rate,
        "levelup_moves": LEVELUP_MOVES.get(pid, [(1, "tackle"), (1, "growl")]),
    }

with open(f"{DATA_DIR}/pokemon_gen1.json", "w", encoding="utf-8") as f:
    json.dump(pokemon_data, f, indent=2, ensure_ascii=False)
print(f"OK pokemon_gen1.json: {len(pokemon_data)} Pokemon")

with open(f"{DATA_DIR}/moves.json", "w", encoding="utf-8") as f:
    json.dump(MOVES, f, indent=2, ensure_ascii=False)
print(f"OK moves.json: {len(MOVES)} movimientos")

with open(f"{DATA_DIR}/type_chart.json", "w", encoding="utf-8") as f:
    json.dump(TYPE_CHART, f, indent=2, ensure_ascii=False)
print(f"OK type_chart.json: tabla de tipos completa")
print("Datos guardados correctamente.")
