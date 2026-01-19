import asyncio
import random
from typing import Dict, List, Optional, Tuple

from models import DROP_TABLE, Enemy, MONSTER_TEMPLATES, Player
from systems.combat import battle
from systems.town import blacksmith_event, merchant_event
from utils.logging import LogBook, log_print


REGION_TABLE: Dict[str, Dict[str, float]] = {
    "초원": {"encounter": 0.75, "merchant": 0.3, "blacksmith": 0.03},
    "동굴": {"encounter": 0.8, "merchant": 0.2, "blacksmith": 0.04},
    "폐허": {"encounter": 0.85, "merchant": 0.15, "blacksmith": 0.06},
}

REGION_DROPS: Dict[str, List[Tuple[str, float]]] = {
    "초원": [("약초", 0.55), ("가죽", 0.3), ("철", 0.15)],
    "동굴": [("철", 0.5), ("가죽", 0.25), ("약초", 0.15)],
    "폐허": [("철", 0.45), ("가죽", 0.2), ("약초", 0.2)],
}

REGION_MONSTERS: Dict[str, List[Tuple[str, int, int, int, int, str, str]]] = {
    "초원": MONSTER_TEMPLATES,
    "동굴": [
        ("석굴 박쥐", 11, 4, 6, 4, "날카로운 울음으로 혼을 흔든다", "깃털 조각"),
        ("바위 골렘", 16, 6, 8, 6, "균열이 빛나는 돌의 거인", "돌 심장"),
    ],
    "폐허": [
        ("망령", 14, 6, 8, 6, "허공을 떠도는 잿빛 그림자", "저주받은 표식"),
        ("녹슨 기사", 18, 7, 10, 8, "과거의 영광이 남은 쇳더미", "녹슨 인장"),
    ],
}


def explore_intro(logbook: LogBook) -> None:
    line = random.choice(
        [
            "먼지와 풀내음이 섞인 바람이 스친다.",
            "갑옷이 부딪히며 작은 쇳소리가 난다.",
            "발소리가 멀어질수록 마을이 희미해진다.",
        ]
    )
    log_print(logbook, line)


def choose_region() -> str:
    roll = random.random()
    if roll < 0.4:
        return "초원"
    if roll < 0.7:
        return "동굴"
    return "폐허"


async def roll_encounter(region: str) -> Optional[Enemy]:
    await asyncio.sleep(0.05)
    chance = REGION_TABLE[region]["encounter"]
    if random.random() < chance:
        name, hp, atk, exp_reward, gold_reward, desc, trophy = random.choice(
            REGION_MONSTERS[region]
        )
        return Enemy(
            name=name,
            hp=hp,
            atk=atk,
            exp_reward=exp_reward,
            gold_reward=gold_reward,
            description=desc,
            trophy=trophy,
        )
    return None


async def roll_drops(region: str) -> List[str]:
    await asyncio.sleep(0.05)
    drops: List[str] = []
    for name, chance in REGION_DROPS.get(region, DROP_TABLE):
        if random.random() < chance:
            drops.append(name)
    return drops


async def roll_event(region: str) -> str:
    await asyncio.sleep(0.05)
    roll = random.random()
    if roll < REGION_TABLE[region]["blacksmith"]:
        return "blacksmith"
    if roll < REGION_TABLE[region]["merchant"]:
        return "merchant"
    return "none"


async def resolve_explore_turn(region: str) -> Tuple[Optional[Enemy], List[str], str]:
    results = await asyncio.gather(
        roll_encounter(region), roll_drops(region), roll_event(region)
    )
    return results[0], results[1], results[2]


def exploration(player: Player, logbook: LogBook) -> None:
    log_print(logbook, "탐험을 시작합니다...")
    explore_intro(logbook)
    region = choose_region()
    log_print(logbook, f"{region}으로 들어갑니다...")
    enemy, drops, event = asyncio.run(resolve_explore_turn(region))

    if enemy is None:
        log_print(logbook, "주변이 조용합니다. 전투가 발생하지 않았습니다.")
    else:
        detail = f" - {enemy.description}" if enemy.description else ""
        log_print(logbook, f"{enemy.name}을(를) 만났다!{detail}")
        won = battle(player, enemy, logbook)
        if won:
            player.exp += enemy.exp_reward
            player.gold += enemy.gold_reward
            log_print(
                logbook,
                f"전투 승리! 경험치 {enemy.exp_reward}, 골드 {enemy.gold_reward} 획득!",
            )
            apply_level_up(player, logbook)
            apply_drops(player, drops, logbook)
            if enemy.trophy:
                log_print(logbook, f"전리품 획득: {enemy.trophy}")
        else:
            log_print(logbook, "패배했습니다. 마을로 돌아갑니다.")

    if event == "merchant":
        merchant_event(player, logbook)
    elif event == "blacksmith":
        blacksmith_event(player, logbook)

    log_print(logbook, "마을로 돌아갑니다...")


def next_level_exp(level: int) -> int:
    return 10 + (level - 1) * 6


def apply_level_up(player: Player, logbook: LogBook) -> None:
    while player.exp >= next_level_exp(player.level):
        player.exp -= next_level_exp(player.level)
        player.level += 1
        player.max_hp += 4
        player.atk += 1
        player.defense += 1
        player.hp = player.max_hp
        log_print(
            logbook,
            f"레벨업! 현재 레벨 {player.level}. 체력/공격/방어가 상승했습니다.",
        )


def apply_drops(player: Player, drops: List[str], logbook: LogBook) -> None:
    if drops:
        for item in drops:
            player.materials[item] += 1
            log_print(logbook, f"재료 획득: {item} +1")
    else:
        log_print(logbook, "재료를 획득하지 못했습니다.")
