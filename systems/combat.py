import random
from typing import Iterator

from models import Enemy, Player
from utils.io import safe_int
from utils.logging import LogBook, log_print


def battle(player: Player, enemy: Enemy, logbook: LogBook) -> bool:
    defending = False
    while enemy.hp > 0 and player.hp > 0:
        log_print(logbook, f"{enemy.name} HP: {enemy.hp} | 내 HP: {player.hp}")
        print("1) 공격 2) 방어 3) 포션 4) 도망")
        choice = safe_int("> ", 1, 4)

        escaped = False
        for line, defending, escaped in player_action_logs(player, enemy, choice, defending):
            log_print(logbook, line)
        if escaped:
            return False
        if enemy.hp <= 0:
            break

        for line in enemy_action_logs(player, enemy, defending):
            log_print(logbook, line)

    return enemy.hp <= 0


def player_action_logs(
    player: Player, enemy: Enemy, action: int, defending: bool
) -> Iterator[tuple[str, bool, bool]]:
    if action == 4:
        if random.random() < 0.5:
            yield "무사히 도망쳤습니다.", False, True
            return
        yield "도망 실패!", False, False
        return

    if action == 2:
        yield "방어 자세를 취합니다.", True, False
        return

    if action == 3:
        if player.potions > 0:
            player.potions -= 1
            heal = min(8, player.max_hp - player.hp)
            player.hp += heal
            yield f"포션을 사용해 체력 {heal} 회복!", False, False
        else:
            yield "포션이 없습니다.", False, False
        return

    damage = max(1, player.atk + player.weapon_level - enemy.atk // 4)
    enemy.hp -= damage
    yield f"{enemy.name}에게 {damage} 피해!", False, False


def enemy_action_logs(player: Player, enemy: Enemy, defending: bool) -> Iterator[str]:
    damage = max(1, enemy.atk - player.defense - player.armor_level)
    if defending:
        damage = max(1, damage // 2)
    player.hp -= damage
    yield f"{enemy.name}의 공격! {damage} 피해를 받았다."
