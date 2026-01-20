import random
from typing import Iterator, Tuple

from models import Enemy, Player, get_equipment_bonus
from utils.io import safe_int
from utils.logging import LogBook, log_print


DEFEND_DAMAGE_MULT: float = 0.5
GUARD_DAMAGE_MULT: float = 0.35
GUARD_ATTACK_BONUS: int = 1
BLEED_DAMAGE: int = 2
BLEED_TURNS: int = 3
BLEED_CHANCE_OFFENSE: float = 0.35
STUN_CHANCE_GUARD: float = 0.25
BOSS_NAME: str = "폐허의 왕"
BOSS_CHARGE_MULT: int = 2
BOSS_ENRAGE_THRESHOLD: float = 0.3
BOSS_ENRAGE_BONUS: int = 2
BOSS_GUARD_REDUCTION: float = 0.5
BOSS_STUN_RESIST_MULT: float = 0.35


def battle(player: Player, enemy: Enemy, logbook: LogBook) -> bool:
    defending = False
    guarding = False
    next_attack_bonus = 0
    boss_charging = False
    boss_guarding = False
    boss_enraged = False
    boss_max_hp = enemy.hp
    boss_intent = "attack"
    player_bleed_turns = 0
    enemy_bleed_turns = 0
    player_stunned = False
    enemy_stunned = False

    while enemy.hp > 0 and player.hp > 0:
        if player_bleed_turns > 0:
            player.hp, player_bleed_turns = apply_bleed_tick(
                player.hp, player_bleed_turns
            )
            log_print(logbook, f"출혈로 {BLEED_DAMAGE} 피해를 받았다.")
            if player.hp <= 0:
                break

        if enemy_bleed_turns > 0:
            enemy.hp, enemy_bleed_turns = apply_bleed_tick(enemy.hp, enemy_bleed_turns)
            log_print(logbook, f"{enemy.name}이(가) 출혈로 피해를 입습니다.")
            if enemy.hp <= 0:
                break

        log_print(logbook, f"{enemy.name} HP: {enemy.hp} | 내 HP: {player.hp}")
        if enemy.name == BOSS_NAME:
            if not boss_enraged and is_boss_enraged(enemy.hp, boss_max_hp):
                boss_enraged = True
                log_print(logbook, "폐허의 왕이 분노합니다!")
            boss_intent, boss_charging, boss_guarding = boss_intent_state(
                boss_charging
            )
            if boss_intent == "charge":
                log_print(logbook, "폐허의 왕이 힘을 모으기 시작합니다.")
            elif boss_intent == "guard":
                log_print(logbook, "폐허의 왕이 방어 태세를 갖춥니다.")
            elif boss_intent == "heavy":
                log_print(logbook, "강력한 일격이 예고됩니다.")

        if player_stunned:
            log_print(logbook, "기절 상태로 행동하지 못했습니다.")
            player_stunned = False
        else:
            print("1) 공격 2) 방어 3) 포션 4) 도망 5) 가드")
            choice = safe_int("> ", 1, 5)

            escaped = False
            for line, defending, escaped, guarding, next_attack_bonus, bleed_applied in (
                player_action_logs(
                    player,
                    enemy,
                    choice,
                    defending,
                    guarding,
                    next_attack_bonus,
                    boss_guarding,
                )
            ):
                log_print(logbook, line)
            if bleed_applied:
                enemy_bleed_turns = BLEED_TURNS
            if escaped:
                return False
            if enemy.hp <= 0:
                break

        if enemy_stunned:
            log_print(logbook, f"{enemy.name}이(가) 기절해 움직이지 못합니다.")
            enemy_stunned = False
        else:
            last_damage = 0
            attacked = False
            for line, damage, did_attack in enemy_action_logs(
                player, enemy, defending, guarding, boss_intent, boss_enraged
            ):
                log_print(logbook, line)
                last_damage = damage
                attacked = did_attack
            if guarding and attacked and last_damage > 0:
                if random.random() < calculate_stun_chance(enemy.name):
                    enemy_stunned = True
                    log_print(logbook, f"{enemy.name}이(가) 잠시 기절합니다.")

    return enemy.hp <= 0


def player_action_logs(
    player: Player,
    enemy: Enemy,
    action: int,
    defending: bool,
    guarding: bool,
    next_attack_bonus: int,
    boss_guarding: bool,
) -> Iterator[Tuple[str, bool, bool, bool, int, bool]]:
    bleed_applied = False
    if action == 4:
        if random.random() < 0.5:
            yield "무사히 도망쳤습니다.", False, True, False, next_attack_bonus, False
            return
        yield "도망 실패!", False, False, False, next_attack_bonus, False
        return

    if action == 2:
        yield "방어 자세를 취합니다.", True, False, False, next_attack_bonus, False
        return

    if action == 5:
        yield "가드로 공격을 대비합니다.", False, False, True, GUARD_ATTACK_BONUS, False
        return

    if action == 3:
        if player.potions > 0:
            player.potions -= 1
            heal = min(8, player.max_hp - player.hp)
            player.hp += heal
            yield (
                f"포션을 사용해 체력 {heal} 회복!",
                False,
                False,
                False,
                next_attack_bonus,
                False,
            )
        else:
            yield "포션이 없습니다.", False, False, False, next_attack_bonus, False
        return

    atk_bonus, _, _ = get_equipment_bonus(player)
    damage = max(
        1,
        player.atk + player.weapon_level + atk_bonus + next_attack_bonus - enemy.atk // 4,
    )
    if boss_guarding:
        damage = apply_boss_guard(damage)
    enemy.hp -= damage
    if player.weapon_tag == "OFFENSE" and random.random() < BLEED_CHANCE_OFFENSE:
        bleed_applied = True
    yield f"{enemy.name}에게 {damage} 피해!", False, False, False, 0, bleed_applied


def enemy_action_logs(
    player: Player,
    enemy: Enemy,
    defending: bool,
    guarding: bool,
    boss_intent: str,
    boss_enraged: bool,
) -> Iterator[Tuple[str, int, bool]]:
    if enemy.name == BOSS_NAME and boss_intent == "charge":
        yield "폐허의 왕이 힘을 응축하고 있습니다.", 0, False
        return
    _, def_bonus, _ = get_equipment_bonus(player)
    raw_damage = max(1, enemy.atk - player.defense - player.armor_level - def_bonus)
    if enemy.name == BOSS_NAME:
        raw_damage += BOSS_ENRAGE_BONUS if boss_enraged else 0
        if boss_intent == "heavy":
            raw_damage *= BOSS_CHARGE_MULT
    damage = apply_damage_reduction(raw_damage, defending, guarding)
    player.hp -= damage
    yield f"{enemy.name}의 공격! {damage} 피해를 받았다.", damage, True


def boss_intent_state(charging: bool) -> Tuple[str, bool, bool]:
    intent = resolve_boss_intent(charging, random.random())
    if intent == "charge":
        return intent, True, False
    if intent == "guard":
        return intent, False, True
    if intent == "heavy":
        return intent, False, False
    return intent, False, False


def resolve_boss_intent(charging: bool, roll: float) -> str:
    if charging:
        return "heavy"
    if roll < 0.25:
        return "charge"
    if roll < 0.5:
        return "guard"
    return "attack"


def is_boss_enraged(hp: int, max_hp: int) -> bool:
    return hp <= max_hp * BOSS_ENRAGE_THRESHOLD


def apply_boss_guard(damage: int) -> int:
    return max(1, int(damage * BOSS_GUARD_REDUCTION))


def apply_damage_reduction(damage: int, defending: bool, guarding: bool) -> int:
    multiplier = 1.0
    if defending:
        multiplier *= DEFEND_DAMAGE_MULT
    if guarding:
        multiplier *= GUARD_DAMAGE_MULT
    return max(1, int(damage * multiplier))


def apply_bleed_tick(hp: int, turns: int) -> Tuple[int, int]:
    hp = max(0, hp - BLEED_DAMAGE)
    return hp, max(0, turns - 1)


def calculate_stun_chance(enemy_name: str) -> float:
    if enemy_name == BOSS_NAME:
        return STUN_CHANCE_GUARD * BOSS_STUN_RESIST_MULT
    return STUN_CHANCE_GUARD
