from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class Player:
    name: str
    level: int = 1
    exp: int = 0
    max_hp: int = 20
    hp: int = 20
    atk: int = 4
    defense: int = 1
    gold: int = 10
    potions: int = 2
    weapon_level: int = 0
    armor_level: int = 0
    weapon_tag: str = "OFFENSE"
    armor_tag: str = "DEFENSE"
    explore_bonus: float = 0.0
    materials: Dict[str, int] = field(
        default_factory=lambda: {"철": 0, "가죽": 0, "약초": 0}
    )


@dataclass
class Enemy:
    name: str
    hp: int
    atk: int
    exp_reward: int
    gold_reward: int
    description: str = ""
    trophy: str = ""


ITEM_SHOP_PRICES: Dict[str, int] = {
    "포션": 5,
    "철": 4,
    "가죽": 3,
    "약초": 2,
}

MATERIAL_SELL_PRICE: int = 2

DROP_TABLE: List[Tuple[str, float]] = [
    ("철", 0.25),
    ("가죽", 0.35),
    ("약초", 0.45),
]

MONSTER_TEMPLATES: List[Tuple[str, int, int, int, int, str, str]] = [
    ("슬라임", 10, 3, 4, 3, "점액질이 흐르는 작은 괴물", "점액 덩어리"),
    ("고블린", 12, 4, 6, 4, "녹슨 단검을 쥔 약탈자", "녹슨 단검"),
    ("늑대", 14, 5, 7, 5, "빛나는 눈빛의 야생 포식자", "거친 송곳니"),
]

BLACKSMITH_RECIPES: Dict[str, Dict[str, int]] = {
    "무기 강화": {"철": 2, "가죽": 1},
    "방어구 강화": {"철": 1, "가죽": 2},
}

BUILD_TAGS: Tuple[str, ...] = ("OFFENSE", "DEFENSE", "EXPLORER")
BUILD_TAG_BONUSES: Dict[str, Tuple[int, int, float]] = {
    "OFFENSE": (1, 0, 0.0),
    "DEFENSE": (0, 1, 0.0),
    "EXPLORER": (0, 0, 0.05),
}


def get_tag_bonus(tag: str) -> Tuple[int, int, float]:
    return BUILD_TAG_BONUSES.get(tag, (0, 0, 0.0))


def get_equipment_bonus(player: Player) -> Tuple[int, int, float]:
    weapon_atk, weapon_def, weapon_exp = get_tag_bonus(player.weapon_tag)
    armor_atk, armor_def, armor_exp = get_tag_bonus(player.armor_tag)
    return weapon_atk + armor_atk, weapon_def + armor_def, weapon_exp + armor_exp
