import asyncio
import random
from dataclasses import dataclass
from typing import Dict, Iterator, List

from utils import event_generator, prompt_int


@dataclass
class Player:
    name: str
    hp: int
    gold: int
    potions: int
    level: int
    exp: int
    weapon_level: int
    materials: Dict[str, int]


@dataclass
class Enemy:
    name: str
    hp: int
    attack: int


class Game:
    def __init__(self) -> None:
        self.player = self._create_player()
        self.running = True

    def run(self) -> None:
        print("작은 RPG에 오신 것을 환영합니다.")
        while self.running:
            print("\n행동을 선택하세요:")
            print("1) 탐험")
            print("2) 휴식")
            print("3) 상태")
            print("4) 종료")
            choice = prompt_int("> ", 1, 4)
            if choice == 1:
                self._explore()
            elif choice == 2:
                self._rest()
            elif choice == 3:
                self._status()
            else:
                self.running = False
                print("모험가여, 안녕히.")

    def _create_player(self) -> Player:
        name = input("영웅의 이름을 입력하세요: ").strip() or "영웅"
        return Player(
            name=name,
            hp=20,
            gold=5,
            potions=1,
            level=1,
            exp=0,
            weapon_level=0,
            materials={"철": 0, "가죽": 0, "약초": 0},
        )

    def _status(self) -> None:
        player = self.player
        print(f"이름: {player.name}")
        print(f"레벨: {player.level}")
        print(f"경험치: {player.exp}/{self._next_level_exp()}")
        print(f"체력: {player.hp}")
        print(f"골드: {player.gold}")
        print(f"포션: {player.potions}")
        print(f"무기 등급: +{player.weapon_level}")
        print(
            "재료: "
            + ", ".join(f"{name} {count}" for name, count in player.materials.items())
        )

    def _explore(self) -> None:
        print("야생으로 발걸음을 옮깁니다...")
        for line in event_generator(self._explore_async()):
            print(line)

        if random.random() < 0.6:
            enemy = self._random_enemy()
            print(f"{enemy.name}가(이) 나타났다!")
            for line in self._combat_log(enemy):
                print(line)
        else:
            print("주변이 조용합니다. 오늘은 적이 없습니다.")
            self._maybe_find_material("약초", 0.5)

        if self.running:
            self._random_encounter()

    def _rest(self) -> None:
        events = [
            "작은 야영지를 세웁니다.",
            "상처를 붕대로 감습니다.",
            "휴식 후 컨디션이 좋아졌습니다.",
        ]
        for line in event_generator(events):
            print(line)
        self.player.hp = min(self.player.hp + 5, 20)

    def _random_enemy(self) -> Enemy:
        options = [
            Enemy(name="슬라임", hp=6, attack=2),
            Enemy(name="고블린", hp=8, attack=3),
            Enemy(name="늑대", hp=7, attack=3),
        ]
        return random.choice(options)

    def _combat_log(self, enemy: Enemy) -> Iterator[str]:
        player = self.player
        while enemy.hp > 0 and player.hp > 0:
            player_hit = random.randint(2, 5) + player.weapon_level
            enemy.hp -= player_hit
            yield f"{enemy.name}에게 {player_hit}의 피해를 입혔습니다."
            if enemy.hp <= 0:
                gold_reward = random.randint(2, 6)
                exp_reward = random.randint(4, 7)
                player.gold += gold_reward
                yield f"{enemy.name}를 쓰러뜨렸습니다. 골드 {gold_reward}을(를) 얻었습니다."
                for line in self._gain_exp(exp_reward):
                    yield line
                self._maybe_find_material(random.choice(["철", "가죽"]), 0.5)
                break

            enemy_hit = random.randint(1, enemy.attack)
            player.hp -= enemy_hit
            yield f"{enemy.name}의 공격! {enemy_hit}의 피해를 받았습니다."
            if player.hp <= 0:
                yield "쓰러졌습니다. 게임 오버."
                self.running = False
                break

            if player.potions > 0 and player.hp <= 5:
                player.potions -= 1
                player.hp += 5
                yield "포션을 마셔 체력 5를 회복했습니다."

    def _gain_exp(self, amount: int) -> Iterator[str]:
        player = self.player
        player.exp += amount
        yield f"경험치 {amount}을(를) 얻었습니다."
        while player.exp >= self._next_level_exp():
            player.exp -= self._next_level_exp()
            player.level += 1
            player.hp = min(player.hp + 5, 25)
            yield f"레벨업! 현재 레벨 {player.level}."

    def _next_level_exp(self) -> int:
        return 10 + (self.player.level - 1) * 5

    def _maybe_find_material(self, name: str, chance: float) -> None:
        if random.random() < chance:
            self.player.materials[name] += 1
            print(f"{name}을(를) 획득했습니다.")

    def _random_encounter(self) -> None:
        roll = random.random()
        if roll < 0.25:
            self._merchant_shop()
        elif roll < 0.28:
            self._blacksmith()

    def _merchant_shop(self) -> None:
        player = self.player
        print("이동 상인을 만났습니다.")
        while True:
            print("\n상점 메뉴:")
            print("1) 포션 구매 (5 골드)")
            print("2) 철 구매 (4 골드)")
            print("3) 가죽 구매 (3 골드)")
            print("4) 재료 판매 (개당 2 골드)")
            print("5) 나가기")
            choice = prompt_int("> ", 1, 5)
            if choice == 1:
                self._buy_item("포션", 5)
            elif choice == 2:
                self._buy_material("철", 4)
            elif choice == 3:
                self._buy_material("가죽", 3)
            elif choice == 4:
                self._sell_materials()
            else:
                print("상인을 떠납니다.")
                break
            print(f"현재 골드: {player.gold}")

    def _buy_item(self, name: str, cost: int) -> None:
        if self.player.gold < cost:
            print("골드가 부족합니다.")
            return
        self.player.gold -= cost
        if name == "포션":
            self.player.potions += 1
        print(f"{name}을(를) 구매했습니다.")

    def _buy_material(self, name: str, cost: int) -> None:
        if self.player.gold < cost:
            print("골드가 부족합니다.")
            return
        self.player.gold -= cost
        self.player.materials[name] += 1
        print(f"{name}을(를) 구매했습니다.")

    def _sell_materials(self) -> None:
        player = self.player
        total = sum(player.materials.values())
        if total == 0:
            print("판매할 재료가 없습니다.")
            return
        print("판매할 재료를 선택하세요:")
        print("1) 철")
        print("2) 가죽")
        print("3) 약초")
        print("4) 취소")
        choice = prompt_int("> ", 1, 4)
        if choice == 4:
            return
        material = ["철", "가죽", "약초"][choice - 1]
        if player.materials[material] <= 0:
            print("재료가 부족합니다.")
            return
        player.materials[material] -= 1
        player.gold += 2
        print(f"{material}을(를) 판매했습니다.")

    def _blacksmith(self) -> None:
        player = self.player
        print("희귀한 대장장이를 만났습니다.")
        print("무기를 강화하려면 철 2개와 가죽 1개가 필요합니다.")
        print("1) 강화하기")
        print("2) 나가기")
        choice = prompt_int("> ", 1, 2)
        if choice == 1:
            if player.materials["철"] >= 2 and player.materials["가죽"] >= 1:
                player.materials["철"] -= 2
                player.materials["가죽"] -= 1
                player.weapon_level += 1
                print(f"무기가 강화되었습니다. 무기 등급 +{player.weapon_level}.")
            else:
                print("재료가 부족합니다.")
        else:
            print("대장장이를 떠납니다.")

    def _explore_async(self) -> List[str]:
        return asyncio.run(self._async_scout_and_loot())

    async def _async_scout_and_loot(self) -> List[str]:
        results = await asyncio.gather(self._async_scout(), self._async_find_loot())
        return list(results)

    async def _async_scout(self) -> str:
        await asyncio.sleep(0.3)
        return "앞을 정찰해 신선한 발자국을 발견했습니다."

    async def _async_find_loot(self) -> str:
        await asyncio.sleep(0.2)
        if random.random() < 0.5:
            self.player.gold += 3
            return "금화 3개가 든 주머니를 찾았습니다."
        return "가치 있는 것을 찾지 못했습니다."
