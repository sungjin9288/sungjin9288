from typing import Dict, List

from models import CRAFT_RECIPES, EQUIPMENT_ITEMS, Equipment, Player
from utils.logging import LogBook, log_print


def can_craft(materials: Dict[str, int], recipe: Dict[str, int]) -> bool:
    return all(materials.get(name, 0) >= count for name, count in recipe.items())


def list_craftable(materials: Dict[str, int]) -> List[str]:
    craftable: List[str] = []
    for item_name, recipe in CRAFT_RECIPES.items():
        if can_craft(materials, recipe):
            craftable.append(item_name)
    return craftable


def list_all_recipes() -> List[str]:
    return list(CRAFT_RECIPES.keys())


def get_equipment(item_name: str) -> Equipment:
    return EQUIPMENT_ITEMS[item_name]


def craft_item(player: Player, item_name: str, logbook: LogBook) -> bool:
    recipe = CRAFT_RECIPES.get(item_name)
    if not recipe or not can_craft(player.materials, recipe):
        log_print(logbook, "재료가 부족합니다.")
        return False
    for material, count in recipe.items():
        player.materials[material] -= count
    item = EQUIPMENT_ITEMS[item_name]
    if item.slot == "weapon":
        player.weapons_owned.append(item.name)
        if not player.weapon_item:
            player.weapon_item = item.name
    else:
        player.armors_owned.append(item.name)
        if not player.armor_item:
            player.armor_item = item.name
    log_print(logbook, f"제작 완료: {item.name}")
    logbook.add(f"DISCOVER_EQUIP:{item.name}")
    return True
