import asyncio
import random
from typing import Dict, List, Optional, Tuple

from models import DROP_TABLE, Enemy, MONSTER_TEMPLATES, Player
from systems.combat import battle
from systems.town import blacksmith_event, merchant_event
from utils.io import safe_int
from utils.logging import LogBook, log_print


REGION_TABLE: Dict[str, Dict[str, float]] = {
    "초원": {"encounter": 0.75, "merchant": 0.3, "blacksmith": 0.03},
    "동굴": {"encounter": 0.8, "merchant": 0.2, "blacksmith": 0.04},
    "폐허": {"encounter": 0.85, "merchant": 0.15, "blacksmith": 0.06},
    "폐허 심층": {"encounter": 1.0, "merchant": 0.0, "blacksmith": 0.0},
}

REGION_REWARD: Dict[str, float] = {"초원": 1.0, "동굴": 1.2, "폐허": 1.4, "폐허 심층": 1.8}

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

BOSS_TEMPLATE: Tuple[str, int, int, int, int, str, str] = (
    "폐허의 왕",
    28,
    9,
    20,
    15,
    "검게 응축된 갑옷과 함께 천천히 다가온다",
    "왕의 심장석",
)

BOSS_ENTRY_LEVEL: int = 6
BOSS_ENTRY_GEAR: int = 2
BOSS_ENTRY_POTIONS: int = 4
DEPTH_MULT_BASE: float = 1.0
DEPTH_MULT_STEP: float = 0.1
DEPTH_MULT_MAX: float = 2.0
BONUS_DROP_MIN_DEPTH: int = 2
BONUS_DROP_ALLOWED_REGIONS: Tuple[str, ...] = ("초원", "동굴", "폐허")


def explore_intro(logbook: LogBook) -> None:
    line = random.choice(
        [
            "먼지와 풀내음이 섞인 바람이 스친다.",
            "갑옷이 부딪히며 작은 쇳소리가 난다.",
            "발소리가 멀어질수록 마을이 희미해진다.",
        ]
    )
    log_print(logbook, line)


def select_region(player: Player) -> str:
    while True:
        print("\n탐험 지역을 선택하세요.")
        print("1) 초원")
        print("2) 동굴")
        print("3) 폐허")
        print("4) 폐허 심층 (보스)")
        choice = safe_int("> ", 1, 4)
        region = ["초원", "동굴", "폐허", "폐허 심층"][choice - 1]
        if region != "폐허 심층":
            return region
        allowed, reason = can_enter_boss(player)
        if allowed:
            return region
        print(reason)


def reward_multiplier(region: str, depth: int) -> float:
    base = REGION_REWARD.get(region, 1.0)
    depth_bonus = DEPTH_MULT_BASE + DEPTH_MULT_STEP * max(0, depth - 1)
    depth_bonus = min(depth_bonus, DEPTH_MULT_MAX)
    return base * depth_bonus


def maybe_add_bonus_drop(region: str, depth: int, drops: List[str]) -> None:
    if not bonus_drop_allowed(region, depth):
        return
    bonus_chance = 0.1 * max(0, depth - 1)
    if random.random() < bonus_chance:
        table = REGION_DROPS.get(region, DROP_TABLE)
        drops.append(random.choice([name for name, _ in table]))


def should_continue(region: str, depth: int) -> bool:
    print(f"\n현재 탐험 단계: {depth}")
    if region == "폐허":
        print("공기가 차갑고 무겁습니다. 더 깊이 들어갈수록 위험해집니다.")
    print("1) 계속 진행")
    print("2) 귀환")
    choice = safe_int("> ", 1, 2)
    return choice == 1


def can_enter_boss(player: Player) -> Tuple[bool, str]:
    if player.level >= BOSS_ENTRY_LEVEL and (
        (player.weapon_level >= BOSS_ENTRY_GEAR and player.armor_level >= BOSS_ENTRY_GEAR)
        or player.potions >= BOSS_ENTRY_POTIONS
    ):
        return True, ""
    return (
        False,
        "보스 진입 조건이 부족합니다. (레벨 6 이상 AND 무기/방어구 +2 또는 포션 4개)",
    )


def bonus_drop_allowed(region: str, depth: int) -> bool:
    return region in BONUS_DROP_ALLOWED_REGIONS and depth >= BONUS_DROP_MIN_DEPTH


async def roll_encounter(region: str) -> Optional[Enemy]:
    await asyncio.sleep(0.05)
    chance = REGION_TABLE[region]["encounter"]
    if random.random() < chance:
        if region == "폐허 심층":
            name, hp, atk, exp_reward, gold_reward, desc, trophy = BOSS_TEMPLATE
        else:
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
    region = select_region(player)
    if region == "폐허 심층":
        log_print(logbook, "이곳부터는 되돌아가기 어렵습니다...")
    log_print(logbook, f"{region}으로 향합니다...")

    depth = 1
    while True:
        enemy, drops, event = asyncio.run(resolve_explore_turn(region))
        maybe_add_bonus_drop(region, depth, drops)
        multiplier = reward_multiplier(region, depth)

        if enemy is None:
            log_print(logbook, "주변이 조용합니다. 전투가 발생하지 않았습니다.")
        else:
            detail = f" - {enemy.description}" if enemy.description else ""
            log_print(logbook, f"{enemy.name}을(를) 만났다!{detail}")
            won = battle(player, enemy, logbook)
            if won:
                exp_reward = max(1, int(enemy.exp_reward * multiplier))
                gold_reward = max(1, int(enemy.gold_reward * multiplier))
                player.exp += exp_reward
                player.gold += gold_reward
                log_print(
                    logbook,
                    f"전투 승리! 경험치 {exp_reward}, 골드 {gold_reward} 획득!",
                )
                apply_level_up(player, logbook)
                apply_drops(player, drops, logbook)
                if enemy.trophy:
                    log_print(logbook, f"전리품 획득: {enemy.trophy}")
                if region == "폐허 심층":
                    log_print(logbook, "폐허의 왕을 쓰러뜨렸습니다. 새로운 엔딩이 열립니다.")
                    boss_ending(logbook)
                    break
            else:
                log_print(logbook, "패배했습니다. 마을로 돌아갑니다.")
                break

        if event == "merchant":
            merchant_event(player, logbook)
        elif event == "blacksmith":
            blacksmith_event(player, logbook)

        if player.hp <= 0:
            break
        if region == "폐허 심층":
            break
        if not should_continue(region, depth):
            break
        log_print(logbook, "더 깊이 들어갑니다...")
        depth += 1

    log_print(logbook, "마을로 돌아갑니다...")


def boss_ending(logbook: LogBook) -> None:
    ending_lines = [
        "엔딩: 폐허의 왕이 쓰러지며 하늘이 밝아진다.",
        "오래된 저주는 옅어지고, 바람에 먼지가 씻겨간다.",
        "이제 이 땅은 다시 사람들의 길이 될 것이다.",
        "당신의 이름이 조용히 전설로 남는다.",
    ]
    for line in ending_lines:
        log_print(logbook, line)


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
