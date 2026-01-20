import random
from typing import Dict, List, Sequence

from models import (
    BUILD_TAGS,
    CRAFT_RECIPES,
    EQUIPMENT_ITEMS,
    EQUIPMENT_SHOP_PRICES,
    EQUIPMENT_TIERS,
    ITEM_SHOP_PRICES,
    MATERIAL_SELL_PRICE,
)

LIST_SELL_RATE: float = 0.5
RECIPE_SELL_RATE: float = 0.5
SHOP_TIER_LIMIT: int = 2
BASE_EQUIPMENT_STOCK: List[str] = [
    "초원의 결의검",
    "초원의 경갑",
    "철벽 단검",
    "철갑 방패",
    "길잡이 활",
    "탐험가 외투",
]


def get_buy_price(item_name: str) -> int:
    if item_name in ITEM_SHOP_PRICES:
        return ITEM_SHOP_PRICES[item_name]
    if item_name in EQUIPMENT_SHOP_PRICES:
        return EQUIPMENT_SHOP_PRICES[item_name]
    raise ValueError(f"Unknown item for buy price: {item_name}")


def get_sell_price(item_name: str) -> int:
    if item_name in EQUIPMENT_SHOP_PRICES:
        return max(1, int(EQUIPMENT_SHOP_PRICES[item_name] * LIST_SELL_RATE))
    if item_name in ITEM_SHOP_PRICES and item_name != "포션":
        return MATERIAL_SELL_PRICE
    recipe = CRAFT_RECIPES.get(item_name)
    if not recipe:
        return 1
    total = _recipe_material_total(recipe)
    return max(1, int(total * RECIPE_SELL_RATE))


def is_shop_tier(item_name: str) -> bool:
    return EQUIPMENT_TIERS.get(item_name, 1) <= SHOP_TIER_LIMIT


def build_rotating_stock(
    rng: random.Random,
    base_stock: Sequence[str],
    previous: Sequence[str] | None = None,
) -> List[str]:
    rotating: List[str] = []
    for tag in BUILD_TAGS:
        candidates = [
            name
            for name, item in EQUIPMENT_ITEMS.items()
            if item.tag == tag and is_shop_tier(name)
        ]
        if previous:
            prev_item = next(
                (name for name in previous if EQUIPMENT_ITEMS[name].tag == tag), ""
            )
            if prev_item in candidates and len(candidates) > 1:
                candidates = [name for name in candidates if name != prev_item]
        if not candidates:
            continue
        rotating.append(rng.choice(candidates))
    return rotating


def merge_stock(base_stock: Sequence[str], rotating_stock: Sequence[str]) -> List[str]:
    seen = set()
    merged: List[str] = []
    for name in list(base_stock) + list(rotating_stock):
        if name in seen:
            continue
        merged.append(name)
        seen.add(name)
    return merged


def _recipe_material_total(recipe: Dict[str, int]) -> int:
    total = 0
    for material, count in recipe.items():
        unit_price = ITEM_SHOP_PRICES.get(material, MATERIAL_SELL_PRICE)
        total += unit_price * count
    return total
