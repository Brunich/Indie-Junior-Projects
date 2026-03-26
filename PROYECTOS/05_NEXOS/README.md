# Pokémon — El Registro Eterno

Godot 4 | GDScript | Open Source Data (PokeAPI)

Fan game completo con mecánicas base de Pokémon Gen 1, construido en Godot 4 con datos abiertos.

## Mecánicas implementadas

### Sistema de batalla por turnos
- Fórmula oficial de daño Gen 3+ (moderna, compatible Gen 1)
- Tabla de tipos completa (18 tipos)
- STAB (Same Type Attack Bonus)
- Efectividad de tipos vs defensas
- Cálculo de precisión y efectos secundarios
- Status: veneno, quemadura, parálisis, sueño, congelación

### Captura de Pokémon
- Fórmula oficial de captura con multiplicadores por:
  - Tipo de Poké Ball (Poké, Great, Ultra, Master)
  - HP restante
  - Status (sleep/freeze bonus)

### Sistema de experiencia
- Crecimiento medium-fast (lv³)
- Ganar EXP al ganar batalla
- Subida de nivel con recálculo de stats
- Bonus HP al subir nivel

### Pokémon individuales
- IVs aleatorios (0-31 por stat)
- Moveset por nivel
- PP (Power Points) por movimiento
- Nickname customizable

### Overworld
- Movimiento en 4 direcciones
- Encuentros en hierba ponderados
- Interacción con NPCs (base)
- Transiciones de mapa

### Bolsa de objetos
- Poké Balls (poke_ball, great_ball, ultra_ball, master_ball)
- Pociones (potion, super_potion, full_restore)
- Antídoto

## Datos open source

- **Pokémon**: 151 Gen 1 desde PokeAPI con stats base
- **Sprites**: Generados procedurales por tipo (placeholder)
  - Originales disponibles en: github.com/PokeAPI/sprites
- **Movimientos**: 24 movimientos principales
- **Tabla de tipos**: Efectividades completas Gen 1

## Pokémon disponibles

### Starters completos
- Bulbasaur, Ivysaur, Venusaur (Grass/Poison)
- Charmander, Charmeleon, Charizard (Fire/Flying)
- Squirtle, Wartortle, Blastoise (Water)

### Otros destacados
- Pikachu/Raichu (Electric)
- Gengar (Ghost/Poison)
- Mewtwo/Mew (Psychic legendarios)
- Dragonite (Dragon/Flying)
- Gyarados (Water/Flying)
- Snorlax (Normal)
- Y 20+ más

## Estructura de directorios

```
05_POKEMON/
├── codigo/
│   ├── PokemonData.gd       # Recurso de Pokémon individual
│   ├── BattleSystem.gd      # Lógica de batalla por turnos
│   ├── BattleUI.gd          # Interfaz de batalla
│   ├── PlayerTrainer.gd     # Datos del entrenador
│   └── OverworldPlayer.gd   # Movimiento en el mundo
├── datos/
│   ├── pokemon_gen1.json    # Stats de 151 Pokémon
│   ├── moves.json           # Movimientos
│   └── type_chart.json      # Tabla de efectividad de tipos
├── sprites/
│   └── pokemon/             # Sprites por ID (1-151)
│       └── {id}.png, {id}_back.png
├── escenas/
│   ├── batalla/
│   ├── overworld/
│   └── ui/
├── audio/
├── shaders/
├── project.godot            # Configuración de Godot 4
└── README.md
```

## Cómo abrir el proyecto

1. Descarga Godot 4.2 o superior
2. Selecciona "Open" → navega a `project.godot`
3. El proyecto se carga con todos los datos y código

## Próximas características

- [ ] Escenas completas (overworld, ciudades, edificios)
- [ ] Sistema de guardado persistente
- [ ] Pokédex interactivo
- [ ] Entrenadores con IA
- [ ] Evolucionesión de Pokémon
- [ ] TMs/HMs (Technical Machines)
- [ ] Árbitro de batalla visual
- [ ] Música y sonidos

## Créditos

- **Datos**: PokeAPI (pokeapi.co) — público bajo licencia CC0
- **Sprites originales**: GitHub PokeAPI/sprites
- **Desarrollo**: IndieStudio Bruno Salas — Godot 4
