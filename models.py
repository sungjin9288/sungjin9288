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
    weapon_item: str = ""
    armor_item: str = ""
    weapons_owned: List[str] = field(default_factory=list)
    armors_owned: List[str] = field(default_factory=list)
    materials: Dict[str, int] = field(
        default_factory=lambda: {
            "약초": 0,
            "야생꽃": 0,
            "사슴뿔": 0,
            "이끼씨앗": 0,
            "은빛꽃잎": 0,
            "철": 0,
            "수정": 0,
            "박쥐날개": 0,
            "광휘석": 0,
            "어둠버섯": 0,
            "고철": 0,
            "망령가루": 0,
            "낡은 인장": 0,
            "망각의 유물": 0,
            "저주의 조각": 0,
            "초원의 정수": 0,
            "심층 광석": 0,
            "부패의 핵": 0,
            "왕의 심장석": 0,
            "심연의 잔재": 0,
        }
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
    "약초": 2,
    "야생꽃": 2,
    "사슴뿔": 3,
    "이끼씨앗": 4,
    "은빛꽃잎": 4,
    "수정": 4,
    "박쥐날개": 3,
    "광휘석": 5,
    "어둠버섯": 4,
    "고철": 4,
    "망령가루": 5,
    "낡은 인장": 5,
    "망각의 유물": 6,
    "저주의 조각": 6,
}

MATERIAL_SELL_PRICE: int = 2

BOSS_MATERIALS: Tuple[str, ...] = ("왕의 심장석", "심연의 잔재")

DROP_TABLE: List[Tuple[str, float]] = [
    ("철", 0.25),
    ("약초", 0.45),
]

MONSTER_TEMPLATES: List[Tuple[str, int, int, int, int, str, str]] = [
    ("슬라임", 10, 3, 4, 3, "점액질이 흐르는 작은 괴물", "점액 덩어리"),
    ("고블린", 12, 4, 6, 4, "녹슨 단검을 쥔 약탈자", "녹슨 단검"),
    ("늑대", 14, 5, 7, 5, "빛나는 눈빛의 야생 포식자", "거친 송곳니"),
    ("들소", 16, 5, 8, 6, "굵은 숨결로 땅을 울린다", "질긴 가죽"),
    ("숲도마뱀", 11, 4, 5, 4, "낙엽 속에서 번뜩이는 눈", "비늘 조각"),
    ("오크", 18, 6, 9, 7, "거친 숨소리가 풀숲을 흔든다", "투박한 도끼"),
    ("미노타우르스", 22, 7, 12, 9, "뿔이 달린 거구가 길을 막는다", "거대한 뿔"),
]

MONSTER_LIST: Tuple[str, ...] = (
    "슬라임",
    "고블린",
    "늑대",
    "들소",
    "숲도마뱀",
    "오크",
    "미노타우르스",
    "석굴 박쥐",
    "좀비 광부",
    "바위 골렘",
    "동굴거미",
    "동굴 수문장",
    "망령",
    "구울",
    "녹슨 기사",
    "뱀파이어",
    "부패한 수호자",
    "폐허의 사도",
    "폐허의 왕",
)

BLACKSMITH_RECIPES: Dict[str, Dict[str, int]] = {
    "무기 강화": {"철": 2, "사슴뿔": 1},
    "방어구 강화": {"고철": 1, "망령가루": 1},
}

BUILD_TAGS: Tuple[str, ...] = ("OFFENSE", "DEFENSE", "EXPLORER")
BUILD_TAG_BONUSES: Dict[str, Tuple[int, int, float]] = {
    "OFFENSE": (1, 0, 0.0),
    "DEFENSE": (0, 1, 0.0),
    "EXPLORER": (0, 0, 0.05),
}


@dataclass
class Equipment:
    name: str
    slot: str
    tag: str
    atk: int
    defense: int
    explore: float
    description: str = ""


EQUIPMENT_ITEMS: Dict[str, Equipment] = {
    "초원의 결의검": Equipment("초원의 결의검", "weapon", "OFFENSE", 2, 0, 0.0),
    "초원의 경갑": Equipment("초원의 경갑", "armor", "OFFENSE", 1, 1, 0.0),
    "피의 전투도끼": Equipment("피의 전투도끼", "weapon", "OFFENSE", 3, 0, 0.0),
    "맹렬한 장창": Equipment("맹렬한 장창", "weapon", "OFFENSE", 3, 0, 0.0),
    "야성의 흉갑": Equipment("야성의 흉갑", "armor", "OFFENSE", 1, 2, 0.0),
    "철벽 단검": Equipment("철벽 단검", "weapon", "DEFENSE", 1, 1, 0.0),
    "철갑 방패": Equipment("철갑 방패", "armor", "DEFENSE", 0, 2, 0.0),
    "심연의 갑옷": Equipment("심연의 갑옷", "armor", "DEFENSE", 0, 3, 0.0),
    "수호자의 철퇴": Equipment("수호자의 철퇴", "weapon", "DEFENSE", 1, 2, 0.0),
    "강철 흉갑": Equipment("강철 흉갑", "armor", "DEFENSE", 0, 3, 0.0),
    "길잡이 활": Equipment("길잡이 활", "weapon", "EXPLORER", 1, 0, 0.05),
    "탐험가 외투": Equipment("탐험가 외투", "armor", "EXPLORER", 0, 1, 0.05),
    "서풍의 지팡이": Equipment("서풍의 지팡이", "weapon", "EXPLORER", 1, 0, 0.1),
    "바람추적 활": Equipment("바람추적 활", "weapon", "EXPLORER", 1, 0, 0.1),
    "길잡이 장화": Equipment("길잡이 장화", "armor", "EXPLORER", 0, 1, 0.1),
    "왕의 대검": Equipment(
        "왕의 대검",
        "weapon",
        "OFFENSE",
        4,
        0,
        0.0,
        "폐허의 왕이 들고 있던 검. 오래된 맹세가 깃들어 있다.",
    ),
    "왕의 수호갑": Equipment(
        "왕의 수호갑",
        "armor",
        "DEFENSE",
        0,
        4,
        0.0,
        "무너진 성벽의 잔해에서 건져낸 갑옷. 마지막 방패의 기억.",
    ),
    "황혼의 망토": Equipment(
        "황혼의 망토",
        "armor",
        "EXPLORER",
        0,
        1,
        0.1,
        "폐허의 먼지가 스민 망토. 길 잃은 자를 인도한다.",
    ),
    "심연의 학살검": Equipment(
        "심연의 학살검",
        "weapon",
        "OFFENSE",
        5,
        0,
        0.0,
        "심연의 잔재로 벼린 검. 적막한 살기가 흘러나온다.",
    ),
    "성흔의 수호구": Equipment(
        "성흔의 수호구",
        "armor",
        "DEFENSE",
        0,
        5,
        0.0,
        "성흔을 품은 보호구. 붕괴의 충격을 견딘다.",
    ),
    "별빛 망토": Equipment(
        "별빛 망토",
        "armor",
        "EXPLORER",
        0,
        1,
        0.15,
        "별빛이 스민 천. 끝없는 탐험의 흔적이 남아 있다.",
    ),
}

CRAFT_RECIPES: Dict[str, Dict[str, int]] = {
    "초원의 결의검": {"사슴뿔": 2, "야생꽃": 1},
    "초원의 경갑": {"야생꽃": 2, "약초": 1},
    "피의 전투도끼": {"철": 1, "사슴뿔": 1, "야생꽃": 1},
    "맹렬한 장창": {"철": 1, "사슴뿔": 2, "이끼씨앗": 1, "초원의 정수": 1},
    "야성의 흉갑": {"사슴뿔": 1, "은빛꽃잎": 2},
    "철벽 단검": {"철": 2, "수정": 1},
    "철갑 방패": {"철": 2, "고철": 1},
    "심연의 갑옷": {"고철": 2, "망령가루": 1, "부패의 핵": 1},
    "수호자의 철퇴": {"철": 1, "광휘석": 1, "어둠버섯": 1, "심층 광석": 1},
    "강철 흉갑": {"철": 1, "고철": 1, "광휘석": 1},
    "길잡이 활": {"약초": 2, "사슴뿔": 1},
    "탐험가 외투": {"약초": 1, "야생꽃": 1, "박쥐날개": 1},
    "서풍의 지팡이": {"수정": 1, "야생꽃": 2},
    "바람추적 활": {"수정": 1, "박쥐날개": 1, "어둠버섯": 1},
    "길잡이 장화": {"약초": 1, "이끼씨앗": 1, "망각의 유물": 1},
    "왕의 대검": {"왕의 심장석": 1, "고철": 2},
    "왕의 수호갑": {"심연의 잔재": 1, "망령가루": 2},
    "황혼의 망토": {"왕의 심장석": 1, "수정": 1, "야생꽃": 1},
    "심연의 학살검": {"왕의 심장석": 1, "저주의 조각": 1, "고철": 1, "부패의 핵": 1},
    "성흔의 수호구": {"심연의 잔재": 1, "망각의 유물": 1, "망령가루": 1, "심층 광석": 1},
    "별빛 망토": {"왕의 심장석": 1, "은빛꽃잎": 1, "망각의 유물": 1, "초원의 정수": 1},
}

EQUIPMENT_SHOP_PRICES: Dict[str, int] = {
    "초원의 결의검": 12,
    "초원의 경갑": 10,
    "피의 전투도끼": 16,
    "맹렬한 장창": 18,
    "야성의 흉갑": 16,
    "철벽 단검": 12,
    "철갑 방패": 12,
    "심연의 갑옷": 16,
    "수호자의 철퇴": 17,
    "강철 흉갑": 17,
    "길잡이 활": 11,
    "탐험가 외투": 11,
    "서풍의 지팡이": 15,
    "바람추적 활": 16,
    "길잡이 장화": 14,
}

EQUIPMENT_TIERS: Dict[str, int] = {
    "초원의 결의검": 1,
    "초원의 경갑": 1,
    "피의 전투도끼": 2,
    "맹렬한 장창": 2,
    "야성의 흉갑": 2,
    "철벽 단검": 1,
    "철갑 방패": 1,
    "심연의 갑옷": 2,
    "수호자의 철퇴": 2,
    "강철 흉갑": 2,
    "길잡이 활": 1,
    "탐험가 외투": 1,
    "서풍의 지팡이": 2,
    "바람추적 활": 2,
    "길잡이 장화": 2,
    "왕의 대검": 3,
    "왕의 수호갑": 3,
    "황혼의 망토": 3,
    "심연의 학살검": 3,
    "성흔의 수호구": 3,
    "별빛 망토": 3,
}


def get_tag_bonus(tag: str) -> Tuple[int, int, float]:
    return BUILD_TAG_BONUSES.get(tag, (0, 0, 0.0))


def get_item_bonus(item_name: str) -> Tuple[int, int, float]:
    item = EQUIPMENT_ITEMS.get(item_name)
    if not item:
        return 0, 0, 0.0
    return item.atk, item.defense, item.explore

def get_equipment_bonus(player: Player) -> Tuple[int, int, float]:
    weapon_atk, weapon_def, weapon_exp = get_tag_bonus(player.weapon_tag)
    armor_atk, armor_def, armor_exp = get_tag_bonus(player.armor_tag)
    item_atk, item_def, item_exp = get_item_bonus(player.weapon_item)
    armor_item_atk, armor_item_def, armor_item_exp = get_item_bonus(player.armor_item)
    total_atk = weapon_atk + armor_atk + item_atk + armor_item_atk
    total_def = weapon_def + armor_def + item_def + armor_item_def
    total_exp = weapon_exp + armor_exp + item_exp + armor_item_exp
    return total_atk, total_def, total_exp
