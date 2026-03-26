#!/usr/bin/env python3
"""Descarga sprites de Pokémon Gen 1 desde PokeAPI sprites GitHub"""
import urllib.request
import os
import time

SPRITE_DIR = "/sessions/eager-funny-fermat/mnt/IA TEAM/PROYECTOS/05_POKEMON/sprites/pokemon"
os.makedirs(SPRITE_DIR, exist_ok=True)

# IDs de los Pokémon que tenemos datos (los que están en pokemon_gen1.json)
POKEMON_IDS = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,
               25,26,39,52,54,63,66,74,94,129,130,133,143,147,148,149,150,151]

BASE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon"

downloaded = 0
failed = []

for pid in POKEMON_IDS:
    # Front sprite (normal)
    front_path = f"{SPRITE_DIR}/{pid}.png"
    if not os.path.exists(front_path):
        url = f"{BASE_URL}/{pid}.png"
        try:
            urllib.request.urlretrieve(url, front_path)
            print(f"OK {pid}.png")
            downloaded += 1
            time.sleep(0.2)  # rate limiting
        except Exception as e:
            print(f"ERR {pid}: {e}")
            failed.append(pid)
    else:
        print(f"SKIP {pid}.png ya existe")

    # Back sprite
    back_path = f"{SPRITE_DIR}/{pid}_back.png"
    if not os.path.exists(back_path):
        url = f"{BASE_URL}/back/{pid}.png"
        try:
            urllib.request.urlretrieve(url, back_path)
            print(f"OK {pid}_back.png")
            time.sleep(0.15)
        except Exception as e:
            print(f"ERR {pid}_back: {e}")

print(f"\nDescargados: {downloaded} | Fallidos: {len(failed)}")
if failed:
    print(f"Fallidos: {failed}")
