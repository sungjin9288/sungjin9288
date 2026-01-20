import json
from pathlib import Path
from typing import Any, Dict, Optional

from models import Player
from systems.achievements import AchievementManager
from systems.dex import DexManager
from utils.logging import LogBook, log_print


SAVE_PATH = Path("savegame.json")


def build_save_data(
    player: Player,
    achievements: AchievementManager,
    dex_manager: DexManager,
    progress: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "version": "2.0",
        "player": {
            "name": player.name,
            "level": player.level,
            "exp": player.exp,
            "max_hp": player.max_hp,
            "hp": player.hp,
            "atk": player.atk,
            "defense": player.defense,
            "gold": player.gold,
            "potions": player.potions,
            "weapon_level": player.weapon_level,
            "armor_level": player.armor_level,
            "weapon_tag": player.weapon_tag,
            "armor_tag": player.armor_tag,
            "weapon_item": player.weapon_item,
            "armor_item": player.armor_item,
            "weapons_owned": player.weapons_owned,
            "armors_owned": player.armors_owned,
            "explore_bonus": player.explore_bonus,
            "materials": player.materials,
        },
        "progress": progress or {"location": "town", "last_region": None, "depth": 0},
        "achievements": sorted(achievements.unlocked),
        "dex": {
            "materials": sorted(dex_manager.materials),
            "equipment": sorted(dex_manager.equipment),
            "monsters": sorted(dex_manager.monsters),
        },
    }


def apply_save_data(
    player: Player,
    achievements: AchievementManager,
    dex_manager: DexManager,
    data: Dict[str, Any],
    logbook: LogBook,
) -> None:
    player_data = data.get("player", {})
    player.name = str(player_data.get("name", player.name))
    player.level = int(player_data.get("level", player.level))
    player.exp = int(player_data.get("exp", player.exp))
    player.max_hp = int(player_data.get("max_hp", player.max_hp))
    player.hp = int(player_data.get("hp", min(player.hp, player.max_hp)))
    player.atk = int(player_data.get("atk", player.atk))
    player.defense = int(player_data.get("defense", player.defense))
    player.gold = int(player_data.get("gold", player.gold))
    player.potions = int(player_data.get("potions", player.potions))
    player.weapon_level = int(player_data.get("weapon_level", player.weapon_level))
    player.armor_level = int(player_data.get("armor_level", player.armor_level))
    player.weapon_tag = str(player_data.get("weapon_tag", player.weapon_tag))
    player.armor_tag = str(player_data.get("armor_tag", player.armor_tag))
    player.weapon_item = str(player_data.get("weapon_item", player.weapon_item))
    player.armor_item = str(player_data.get("armor_item", player.armor_item))
    weapons_owned = player_data.get("weapons_owned", player.weapons_owned)
    if isinstance(weapons_owned, list):
        player.weapons_owned = [str(item) for item in weapons_owned]
    armors_owned = player_data.get("armors_owned", player.armors_owned)
    if isinstance(armors_owned, list):
        player.armors_owned = [str(item) for item in armors_owned]
    player.explore_bonus = float(player_data.get("explore_bonus", player.explore_bonus))
    materials = player_data.get("materials", player.materials)
    if isinstance(materials, dict):
        for key, value in materials.items():
            player.materials[str(key)] = int(value)
    player.hp = max(1, min(player.hp, player.max_hp))

    achievements_list = data.get("achievements", [])
    if isinstance(achievements_list, list):
        achievements.set_unlocked([str(item) for item in achievements_list])
        achievements.save()
    dex_data = data.get("dex", {})
    if isinstance(dex_data, dict):
        materials = dex_data.get("materials", [])
        equipment = dex_data.get("equipment", [])
        monsters = dex_data.get("monsters", [])
        if isinstance(materials, list) and isinstance(equipment, list) and isinstance(monsters, list):
            dex_manager.set_state(
                [str(item) for item in materials],
                [str(item) for item in equipment],
                [str(item) for item in monsters],
            )

    log_print(logbook, "저장 데이터를 불러왔습니다. 마을에서 다시 시작합니다.")


def save_game(
    player: Player,
    achievements: AchievementManager,
    dex_manager: DexManager,
    logbook: LogBook,
    path: Path = SAVE_PATH,
) -> None:
    data = build_save_data(player, achievements, dex_manager)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log_print(logbook, "게임을 저장했습니다.")


def load_game(
    player: Player,
    achievements: AchievementManager,
    dex_manager: DexManager,
    logbook: LogBook,
    path: Path = SAVE_PATH,
) -> bool:
    if not path.exists():
        log_print(logbook, "저장 파일이 없습니다.")
        return False
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        log_print(logbook, "저장 파일을 읽을 수 없습니다.")
        return False
    if not isinstance(data, dict):
        log_print(logbook, "저장 파일 형식이 올바르지 않습니다.")
        return False
    apply_save_data(player, achievements, dex_manager, data, logbook)
    return True
