import json
from pathlib import Path
from typing import Any, Dict, Optional

from models import Player
from systems.achievements import AchievementManager
from utils.logging import LogBook, log_print


SAVE_PATH = Path("savegame.json")


def build_save_data(
    player: Player,
    achievements: AchievementManager,
    progress: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "version": "1.6",
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
            "explore_bonus": player.explore_bonus,
            "materials": player.materials,
        },
        "progress": progress or {"location": "town", "last_region": None, "depth": 0},
        "achievements": sorted(achievements.unlocked),
    }


def apply_save_data(
    player: Player,
    achievements: AchievementManager,
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

    log_print(logbook, "저장 데이터를 불러왔습니다. 마을에서 다시 시작합니다.")


def save_game(
    player: Player,
    achievements: AchievementManager,
    logbook: LogBook,
    path: Path = SAVE_PATH,
) -> None:
    data = build_save_data(player, achievements)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log_print(logbook, "게임을 저장했습니다.")


def load_game(
    player: Player,
    achievements: AchievementManager,
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
    apply_save_data(player, achievements, data, logbook)
    return True
