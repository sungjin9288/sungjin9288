import asyncio
import random
from typing import Dict, List, Optional, Tuple

from models import DROP_TABLE, Enemy, EQUIPMENT_ITEMS, MONSTER_TEMPLATES, Player, get_equipment_bonus
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

REGION_REWARD: Dict[str, float] = {
    "초원": 1.0,
    "동굴": 1.2,
    "폐허": 1.4,
    "폐허 심층": 1.8,
}

REGION_TRAITS: Dict[str, str] = {
    "초원": "초원은 비교적 안전하지만 보상은 낮습니다.",
    "동굴": "동굴은 전투 압박이 높지만 재료 가치가 오릅니다.",
    "폐허": "폐허는 위험이 크고 희귀 드랍을 기대할 수 있습니다.",
    "폐허 심층": "폐허 심층은 귀환이 어렵고 보스와의 조우가 강제됩니다.",
}

CONQUEST_LOG_PREFIX: str = "REGION_CONQUEST:"
REGION_CONQUEST_BONUS: Dict[str, Tuple[str, float]] = {
    "초원": ("초원의 정수", 0.15),
    "동굴": ("심층 광석", 0.15),
    "폐허": ("부패의 핵", 0.15),
}
MINIBOSS_BY_REGION: Dict[str, str] = {
    "초원": "미노타우르스",
    "동굴": "동굴 수문장",
    "폐허": "폐허의 사도",
}

REGION_DROPS: Dict[str, List[Tuple[str, float]]] = {
    "초원": [("약초", 0.4), ("야생꽃", 0.35), ("사슴뿔", 0.25), ("이끼씨앗", 0.18), ("은빛꽃잎", 0.12)],
    "동굴": [("철", 0.4), ("수정", 0.3), ("박쥐날개", 0.25), ("광휘석", 0.18), ("어둠버섯", 0.15)],
    "폐허": [("고철", 0.4), ("망령가루", 0.3), ("낡은 인장", 0.25), ("망각의 유물", 0.18), ("저주의 조각", 0.12)],
    "폐허 심층": [("왕의 심장석", 0.8), ("심연의 잔재", 0.5)],
}

REGION_MONSTERS: Dict[str, List[Tuple[str, int, int, int, int, str, str]]] = {
    "초원": MONSTER_TEMPLATES,
    "동굴": [
        ("석굴 박쥐", 11, 4, 6, 4, "날카로운 울음으로 혼을 흔든다", "깃털 조각"),
        ("좀비 광부", 13, 5, 7, 5, "녹슨 곡괭이를 끌며 다가온다", "빛바랜 곡괭이"),
        ("바위 골렘", 16, 6, 8, 6, "균열이 빛나는 돌의 거인", "돌 심장"),
        ("동굴거미", 12, 5, 7, 5, "어둠 속에서 조용히 다가온다", "거미줄"),
        ("동굴 수문장", 20, 7, 12, 9, "검은 돌갑옷이 길을 막는다", "수문장의 핵"),
    ],
    "폐허": [
        ("망령", 14, 6, 8, 6, "허공을 떠도는 잿빛 그림자", "저주받은 표식"),
        ("구울", 15, 6, 9, 7, "썩은 숨결이 어둠을 타고 흐른다", "부패한 이빨"),
        ("녹슨 기사", 18, 7, 10, 8, "과거의 영광이 남은 쇳더미", "녹슨 인장"),
        ("뱀파이어", 19, 7, 11, 9, "핏빛 망토가 그림자처럼 스친다", "붉은 송곳니"),
        ("부패한 수호자", 20, 7, 11, 9, "썩어가는 갑옷이 끙끙거린다", "부식된 파편"),
        ("폐허의 사도", 22, 8, 13, 10, "깨진 성소의 신음이 들린다", "검은 부적"),
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
LEVEL_UP_CHOICES: Tuple[str, ...] = ("공격형", "생존형", "탐험형")
LEVEL_UP_ATK_GAIN: int = 2
LEVEL_UP_DEF_GAIN: int = 1
LEVEL_UP_HP_GAIN: int = 5
LEVEL_UP_EXPLORE_GAIN: float = 0.05


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


def reward_multiplier(region: str, depth: int, player: Player) -> float:
    base = REGION_REWARD.get(region, 1.0)
    depth_bonus = DEPTH_MULT_BASE + DEPTH_MULT_STEP * max(0, depth - 1)
    depth_bonus = min(depth_bonus, DEPTH_MULT_MAX)
    explore_bonus = 1.0 + get_explore_bonus_total(player)
    return base * depth_bonus * explore_bonus


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

def is_region_conquered(logbook: LogBook, region: str) -> bool:
    marker = f"{CONQUEST_LOG_PREFIX}{region}"
    return marker in logbook.entries

def get_conquest_bonus(region: str, logbook: LogBook) -> Optional[Tuple[str, float]]:
    if is_region_conquered(logbook, region):
        return REGION_CONQUEST_BONUS.get(region)
    return None


def true_ending_ready(player: Player, logbook: LogBook) -> bool:
    conquered = all(
        is_region_conquered(logbook, region) for region in ("초원", "동굴", "폐허")
    )
    if not conquered:
        return False
    materials_found = {
        line[len("DISCOVER_MATERIAL:") :].strip()
        for line in logbook.entries
        if line.startswith("DISCOVER_MATERIAL:")
    }
    equipment_found = {
        line[len("DISCOVER_EQUIP:") :].strip()
        for line in logbook.entries
        if line.startswith("DISCOVER_EQUIP:")
    }
    total = len(player.materials) + len(EQUIPMENT_ITEMS)
    found = len(materials_found) + len(equipment_found)
    dex_ratio = found / total if total else 0.0
    boss_cleared = any(
        line == "KILL_BOSS:폐허의 왕" for line in logbook.entries
    )
    return dex_ratio >= 0.8 and boss_cleared


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


async def roll_drops(region: str, explore_bonus: float, bonus: Optional[Tuple[str, float]] = None) -> List[str]:
    await asyncio.sleep(0.05)
    drops: List[str] = []
    for name, chance in REGION_DROPS.get(region, DROP_TABLE):
        adjusted = min(0.95, chance + explore_bonus)
        if random.random() < adjusted:
            drops.append(name)
    if bonus:
        bonus_name, bonus_chance = bonus
        adjusted = min(0.95, bonus_chance)
        if random.random() < adjusted:
            drops.append(bonus_name)
    return drops


async def roll_event(region: str) -> str:
    await asyncio.sleep(0.05)
    roll = random.random()
    if roll < REGION_TABLE[region]["blacksmith"]:
        return "blacksmith"
    if roll < REGION_TABLE[region]["merchant"]:
        return "merchant"
    return "none"


async def resolve_explore_turn(region: str, explore_bonus: float, bonus: Optional[Tuple[str, float]] = None) -> Tuple[Optional[Enemy], List[str], str]:
    results = await asyncio.gather(
        roll_encounter(region),
        roll_drops(region, explore_bonus, bonus),
        roll_event(region),
    )
    return results[0], results[1], results[2]


def exploration(player: Player, logbook: LogBook) -> None:
    log_print(logbook, "탐험을 시작합니다...")
    explore_intro(logbook)
    region = select_region(player)

    log_print(logbook, REGION_TRAITS.get(region, ""))
    true_ending_active = False
    if region == "폐허 심층" and true_ending_ready(player, logbook):
        log_print(logbook, "균열이 열린다.")
        if "TRUE_ENDING_UNLOCKED" not in logbook.entries:
            logbook.add("TRUE_ENDING_UNLOCKED")
        print("1) 진엔딩 전투 진입 2) 철수")
        choice = safe_int("> ", 1, 2)
        if choice == 2:
            log_print(logbook, "균열 앞에서 물러섭니다.")
            log_print(logbook, "마을로 돌아갑니다...")
            return
        true_ending_active = True
    if region == "폐허 심층":
        log_print(logbook, "이곳부터는 되돌아가기 어렵습니다...")
    log_print(logbook, f"{region}으로 향합니다...")

    depth = 1
    while True:
        enemy, drops, event = asyncio.run(
            resolve_explore_turn(region, get_explore_bonus_total(player), get_conquest_bonus(region, logbook))
        )
        maybe_add_bonus_drop(region, depth, drops)
        multiplier = reward_multiplier(region, depth, player)

        if enemy is None:
            log_print(logbook, "주변이 조용합니다. 전투가 발생하지 않았습니다.")
        else:
            detail = f" - {enemy.description}" if enemy.description else ""
            log_print(logbook, f"{enemy.name}을(를) 만났다!{detail}")
            logbook.add(f"DISCOVER_MONSTER:{enemy.name}")
            won = battle(player, enemy, logbook)
            if won:
                if region == "폐허 심층" and true_ending_active:
                    log_print(logbook, "균열이 갈라지며 폐허의 왕이 다시 일어선다.")
                    phase_enemy = Enemy(
                        name=enemy.name,
                        hp=max(1, int(enemy.hp * 1.3)),
                        atk=max(1, int(enemy.atk * 1.3)),
                        exp_reward=enemy.exp_reward,
                        gold_reward=enemy.gold_reward,
                        description=enemy.description,
                        trophy=enemy.trophy,
                    )
                    won = battle(player, phase_enemy, logbook, phase_two=True)
                    if not won:
                        log_print(logbook, "패배했습니다. 마을로 돌아갑니다.")
                        break
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
                if (
                    region in MINIBOSS_BY_REGION
                    and enemy.name == MINIBOSS_BY_REGION[region]
                    and not is_region_conquered(logbook, region)
                ):
                    if region == "초원":
                        log_print(
                            logbook,
                            "초원의 위협이 사라졌다. 이곳의 숨겨진 자원들이 모습을 드러낸다.",
                        )
                    elif region == "동굴":
                        log_print(
                            logbook,
                            "동굴의 심층이 열렸다. 이제 더 깊은 광맥을 채굴할 수 있다.",
                        )
                    elif region == "폐허":
                        log_print(
                            logbook,
                            "폐허의 균형이 무너졌다. 부패 속에서 새로운 힘이 스며나온다.",
                        )
                    logbook.add(f"{CONQUEST_LOG_PREFIX}{region}")
                if enemy.trophy:
                    log_print(logbook, f"전리품 획득: {enemy.trophy}")
                if region == "폐허 심층":
                    logbook.add(f"KILL_BOSS:{enemy.name}")
                    if true_ending_active:
                        logbook.add("TRUE_ENDING_CLEAR")
                        log_print(logbook, "진엔딩: 균열이 닫히며 남은 잔재가 사라집니다.")
                        log_print(logbook, "진엔딩: 더 이상 어둠의 잔향이 남지 않습니다.")
                        log_print(logbook, "진엔딩: 마을에는 새로운 평온이 찾아옵니다.")
                    else:
                        log_print(logbook, "폐허의 왕을 쓰러뜨렸습니다. 새로운 엔딩이 열립니다.")
                        boss_ending(logbook, player)
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


def boss_ending(logbook: LogBook, player: Player) -> None:
    materials_found = {
        line[len("DISCOVER_MATERIAL:") :].strip()
        for line in logbook.entries
        if line.startswith("DISCOVER_MATERIAL:")
    }
    equipment_found = {
        line[len("DISCOVER_EQUIP:") :].strip()
        for line in logbook.entries
        if line.startswith("DISCOVER_EQUIP:")
    }
    material_complete = set(player.materials.keys()).issubset(materials_found)
    equipment_complete = set(EQUIPMENT_ITEMS.keys()).issubset(equipment_found)
    if player.weapon_tag == player.armor_tag:
        build_line = f"??? {player.weapon_tag}? ?? ??? ?????."
    else:
        build_line = f"??? {player.weapon_tag}? {player.armor_tag} ???? ?? ?????."
    tactics_line = ""
    if any("??? ??? ?????." in line for line in logbook.entries):
        tactics_line = "??? ?? ?? ???? ??? ?????."
    elif any("??" in line for line in logbook.entries):
        tactics_line = "??? ??? ??? ??????."
    elif any("??" in line for line in logbook.entries):
        tactics_line = "??? ??? ??? ??????."
    dex_line = "??? ??? ??? ???? ???." if material_complete and equipment_complete else "?? ?? ??? ??? ?????."
    ending_lines = [
        "??: ??? ?? ???? ??? ???.",
        build_line,
        dex_line,
        tactics_line or "??? ???? ??? ????.",
        "?? ??? ??? ?? ???.",
    ]
    for line in ending_lines:
        log_print(logbook, line)


def next_level_exp(level: int) -> int:
    return 10 + (level - 1) * 6


def apply_level_up(player: Player, logbook: LogBook) -> None:
    while player.exp >= next_level_exp(player.level):
        player.exp -= next_level_exp(player.level)
        player.level += 1
        player.hp = player.max_hp
        log_print(logbook, f"레벨업! 현재 레벨 {player.level}.")
        apply_level_up_choice(player, logbook)


def apply_level_up_choice(player: Player, logbook: LogBook) -> None:
    print("레벨업 선택지를 고르세요.")
    print("1) 공격형")
    print("2) 생존형")
    print("3) 탐험형")
    choice = safe_int("> ", 1, 3)
    selected = LEVEL_UP_CHOICES[choice - 1]
    apply_level_up_selection(player, selected, logbook)


def apply_level_up_selection(player: Player, selection: str, logbook: LogBook) -> None:
    if selection == "공격형":
        player.atk += LEVEL_UP_ATK_GAIN
        log_print(logbook, "공격력이 상승했습니다.")
    elif selection == "생존형":
        player.defense += LEVEL_UP_DEF_GAIN
        player.max_hp += LEVEL_UP_HP_GAIN
        player.hp = player.max_hp
        log_print(logbook, "방어력과 최대 체력이 상승했습니다.")
    else:
        player.explore_bonus += LEVEL_UP_EXPLORE_GAIN
        log_print(logbook, "탐험 감각이 날카로워졌습니다.")


def get_explore_bonus_total(player: Player) -> float:
    _, _, equip_bonus = get_equipment_bonus(player)
    return player.explore_bonus + equip_bonus


def apply_drops(player: Player, drops: List[str], logbook: LogBook) -> None:
    if drops:
        for item in drops:
            player.materials[item] += 1
            log_print(logbook, f"재료 획득: {item} +1")
            logbook.add(f"DISCOVER_MATERIAL:{item}")
    else:
        log_print(logbook, "재료를 획득하지 못했습니다.")
