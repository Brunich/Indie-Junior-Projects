extends Node

## InventorySystem - Item management singleton

const CreatureInstance = preload("res://codigo/recursos/creature_instance.gd")

enum ItemCategory {
	HEALING,
	BATTLE,
	KEY,
	TM
}

## Item database with all available items
const ITEMS = {
	"potion": {
		"name": "Suero rojo",
		"desc": "Recupera 20 de aguante para una criatura.",
		"category": ItemCategory.HEALING,
		"value": 20,
		"price": 180,
		"effect": "heal_flat",
		"amount": 20
	},
	"super_potion": {
		"name": "Suero fuerte",
		"desc": "Recupera 50 de aguante para una criatura.",
		"category": ItemCategory.HEALING,
		"value": 50,
		"price": 450,
		"effect": "heal_flat",
		"amount": 50
	},
	"antidote": {
		"name": "Antiveneno",
		"desc": "Le quita el veneno a una criatura.",
		"category": ItemCategory.HEALING,
		"value": 0,
		"price": 120,
		"effect": "cure_status",
		"status": "PSN"
	},
	"paralyze_heal": {
		"name": "Desentumidor",
		"desc": "Le quita la parálisis a una criatura.",
		"category": ItemCategory.HEALING,
		"value": 0,
		"price": 120,
		"effect": "cure_status",
		"status": "PAR"
	},
	"revive": {
		"name": "Reanimante",
		"desc": "Levanta a una criatura agotada con la mitad de aguante.",
		"category": ItemCategory.HEALING,
		"value": 0,
		"price": 900,
		"effect": "revive",
		"amount": 0.5
	},
	"poke_biscuit": {
		"name": "Bocado de monte",
		"desc": "Un antojo oloroso; varias criaturas se arriman nomas de sentirlo.",
		"category": ItemCategory.BATTLE,
		"value": 0,
		"effect": "none"
	},
	"catnip_street": {
		"name": "Catnip",
		"desc": "La base de toda captura. Un manojo sencillo que calma a las criaturas si ya vienen cansadas.",
		"category": ItemCategory.BATTLE,
		"value": 0,
		"price": 90,
		"effect": "capture_catnip",
		"catch_multiplier": 1.0,
		"bond_seed": 70
	},
	"catnip_field": {
		"name": "Catnip de alta calidad",
		"desc": "Secado fino y aroma mas estable. Sube bastante la chance de vinculo.",
		"category": ItemCategory.BATTLE,
		"value": 0,
		"price": 180,
		"effect": "capture_catnip",
		"catch_multiplier": 1.65,
		"bond_seed": 105
	},
	"catnip_royal": {
		"name": "Catnip tigre",
		"desc": "Una mezcla premium que amarra el vinculo al instante. No falla.",
		"category": ItemCategory.BATTLE,
		"value": 0,
		"price": 720,
		"effect": "capture_catnip",
		"guaranteed_capture": true,
		"catch_multiplier": 3.4,
		"bond_seed": 135
	},
	"scar_shard": {
		"name": "Scar Shard",
		"desc": "Una esquirla rara. Se nota que venia de algo mas grande.",
		"category": ItemCategory.KEY,
		"value": 0,
		"effect": "none"
	},
	"ember_stone": {
		"name": "Ember Stone",
		"desc": "Una piedra con lumbre por dentro. Late calientita.",
		"category": ItemCategory.KEY,
		"value": 0,
		"effect": "none"
	}
}

## Current inventory: { item_id: quantity }
var inventory: Dictionary = {}
const SHOP_STOCK := ["potion", "antidote", "paralyze_heal", "super_potion", "catnip_street", "catnip_field"]

func _ready() -> void:
	name = "InventorySystem"

## Add item(s) to inventory
func add_item(item_id: String, qty: int = 1) -> void:
	if not ITEMS.has(item_id):
		push_error("InventorySystem: Unknown item ID: ", item_id)
		return

	if not inventory.has(item_id):
		inventory[item_id] = 0

	inventory[item_id] += qty
	print("InventorySystem: Added ", qty, "x ", ITEMS[item_id]["name"])

## Remove item(s) from inventory. Returns true if successful.
func remove_item(item_id: String, qty: int = 1) -> bool:
	if not inventory.has(item_id) or inventory[item_id] < qty:
		print("InventorySystem: Not enough of ", item_id)
		return false

	inventory[item_id] -= qty

	if inventory[item_id] <= 0:
		inventory.erase(item_id)

	print("InventorySystem: Removed ", qty, "x ", ITEMS[item_id]["name"])
	return true

## Check if we have enough of an item
func has_item(item_id: String, qty: int = 1) -> bool:
	return inventory.get(item_id, 0) >= qty

## Get quantity of an item
func get_quantity(item_id: String) -> int:
	return inventory.get(item_id, 0)

func get_price(item_id: String) -> int:
	if not ITEMS.has(item_id):
		return 0
	return int(ITEMS[item_id].get("price", 0))

func get_snapshot() -> Dictionary:
	return inventory.duplicate(true)

func set_snapshot(snapshot: Dictionary) -> void:
	inventory = snapshot.duplicate(true)

func can_use_item_on(item_id: String, target_creature: CreatureInstance) -> bool:
	if target_creature == null:
		return false
	if not ITEMS.has(item_id):
		return false
	var item_data: Dictionary = ITEMS[item_id]
	match String(item_data.get("effect", "")):
		"heal_flat":
			return target_creature.hp_cur > 0 and target_creature.hp_cur < target_creature.hp_max
		"cure_status":
			var status_tag := String(item_data.get("status", ""))
			var expected_status := CreatureInstance.Status.POISONED
			if status_tag == "PAR":
				expected_status = CreatureInstance.Status.PARALYZED
			return target_creature.status == expected_status
		"revive":
			return target_creature.hp_cur <= 0
		"capture_catnip":
			return false
		_:
			return true

## Use an item on a target creature. Returns result message.
func use_item(item_id: String, target_creature: CreatureInstance) -> String:
	if not ITEMS.has(item_id):
		return "Objeto desconocido"

	if not has_item(item_id):
		return "Ya no queda de ese objeto"

	var item_data = ITEMS[item_id]
	var result_msg = ""
	var consumed := true

	match item_data["effect"]:
		"heal_flat":
			if target_creature.hp_cur >= target_creature.hp_max or target_creature.hp_cur <= 0:
				consumed = false
				result_msg = "No hizo falta usarlo."
				return result_msg
			var old_hp = target_creature.hp_cur
			target_creature.hp_cur = min(target_creature.hp_cur + item_data["amount"], target_creature.hp_max)
			result_msg = "%s recupero %d HP!" % [
				target_creature.display_name(),
				target_creature.hp_cur - old_hp
			]

		"cure_status":
			var expected_status := CreatureInstance.Status.POISONED
			if item_data["status"] == "PAR":
				expected_status = CreatureInstance.Status.PARALYZED
			if target_creature.status == expected_status:
				target_creature.status = CreatureInstance.Status.NONE
				result_msg = "Se alivio el malestar de %s." % target_creature.display_name()
			else:
				consumed = false
				result_msg = "No hizo efecto."

		"revive":
			if target_creature.hp_cur == 0:
				var heal_amount = int(target_creature.hp_max * item_data["amount"])
				target_creature.hp_cur = max(1, heal_amount)
				result_msg = "%s volvio al tiro!" % target_creature.display_name()
			else:
				consumed = false
				result_msg = "Esa criatura sigue en pie."

		"none":
			result_msg = "Usaste " + item_data["name"] + "."

		_:
			consumed = false
			result_msg = "Ese efecto todavia no jala"

	if consumed:
		remove_item(item_id, 1)
	return result_msg

## Get all items of a specific category
func get_items_by_category(category: ItemCategory) -> Array:
	var result = []

	for item_id in ITEMS.keys():
		if ITEMS[item_id]["category"] == category:
			result.append(item_id)

	return result

func get_battle_usable_items() -> Array[String]:
	var result: Array[String] = []
	for item_id in inventory.keys():
		if not ITEMS.has(item_id):
			continue
		var item_data: Dictionary = ITEMS[item_id]
		if item_data.get("category") != ItemCategory.BATTLE and item_data.get("category") != ItemCategory.HEALING:
			continue
		result.append(String(item_id))
	result.sort()
	return result
