from typing import Iterable, Set, Tuple

from models import EQUIPMENT_ITEMS, MONSTER_LIST, Player
from utils.logging import LogBook, log_print


MATERIAL_PREFIX: str = "DISCOVER_MATERIAL:"
EQUIP_PREFIX: str = "DISCOVER_EQUIP:"
MONSTER_PREFIX: str = "DISCOVER_MONSTER:"
BOSS_PREFIX: str = "KILL_BOSS:"
MATERIAL_REWARD_LOG: str = "도감 보상: 재료 도감 완성"
MATERIAL_REWARD_GOLD: int = 8
EQUIPMENT_REWARD_LOG: str = "도감 보상: 장비 도감 완성"
EQUIPMENT_REWARD_GOLD: int = 10


class DexManager:
    def __init__(
        self,
        materials: Iterable[str] | None = None,
        equipment: Iterable[str] | None = None,
        monsters: Iterable[str] | None = None,
    ) -> None:
        self.materials: Set[str] = set(materials or [])
        self.equipment: Set[str] = set(equipment or [])
        self.monsters: Set[str] = set(monsters or [])

    def process(self, logbook: LogBook) -> None:
        for line in logbook.entries:
            self._apply_line(line)

    def _apply_line(self, line: str) -> None:
        if line.startswith(MATERIAL_PREFIX):
            self.materials.add(line[len(MATERIAL_PREFIX) :].strip())
            return
        if line.startswith(EQUIP_PREFIX):
            self.equipment.add(line[len(EQUIP_PREFIX) :].strip())
            return
        if line.startswith(MONSTER_PREFIX):
            self.monsters.add(line[len(MONSTER_PREFIX) :].strip())
            return
        if line.startswith(BOSS_PREFIX):
            self.monsters.add(line[len(BOSS_PREFIX) :].strip())

    def set_state(
        self, materials: Iterable[str], equipment: Iterable[str], monsters: Iterable[str]
    ) -> None:
        self.materials = set(materials)
        self.equipment = set(equipment)
        self.monsters = set(monsters)

    def get_state(self) -> Tuple[Set[str], Set[str], Set[str]]:
        return self.materials, self.equipment, self.monsters


def build_material_catalog(player: Player) -> Iterable[str]:
    return list(player.materials.keys())


def build_equipment_catalog() -> Iterable[str]:
    return list(EQUIPMENT_ITEMS.keys())


def build_monster_catalog() -> Iterable[str]:
    return list(MONSTER_LIST)


def apply_material_completion_reward(
    player: Player, dex_manager: DexManager, logbook: LogBook
) -> None:
    if any(MATERIAL_REWARD_LOG in line for line in logbook.entries):
        return
    catalog = set(build_material_catalog(player))
    if not catalog:
        return
    if catalog.issubset(dex_manager.materials):
        player.gold += MATERIAL_REWARD_GOLD
        log_print(
            logbook,
            f"{MATERIAL_REWARD_LOG} (+{MATERIAL_REWARD_GOLD} 골드)",
        )


def apply_equipment_completion_reward(
    player: Player, dex_manager: DexManager, logbook: LogBook
) -> None:
    if any(EQUIPMENT_REWARD_LOG in line for line in logbook.entries):
        return
    catalog = set(build_equipment_catalog())
    if not catalog:
        return
    if catalog.issubset(dex_manager.equipment):
        player.gold += EQUIPMENT_REWARD_GOLD
        log_print(
            logbook,
            f"{EQUIPMENT_REWARD_LOG} (+{EQUIPMENT_REWARD_GOLD} 골드)",
        )
