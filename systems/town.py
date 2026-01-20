
from models import (
    BLACKSMITH_RECIPES,
    BUILD_TAGS,
    ITEM_SHOP_PRICES,
    MATERIAL_SELL_PRICE,
    Player,
)
from systems.achievements import AchievementManager
from systems.quests import QuestManager
from systems.save import load_game, save_game
from utils.io import safe_int
from utils.logging import LogBook, log_print


def show_status(player: Player) -> None:
    print("\n[상태]")
    print(f"이름: {player.name}")
    print(f"레벨: {player.level} (EXP {player.exp}/{next_level_exp(player.level)})")
    print(f"체력: {player.hp}/{player.max_hp}")
    print(f"공격: {player.atk} (무기 +{player.weapon_level})")
    print(f"방어: {player.defense} (방어구 +{player.armor_level})")
    print(f"골드: {player.gold}")
    print(f"포션: {player.potions}")


def show_inventory(player: Player) -> None:
    print("\n[인벤토리]")
    for name, count in player.materials.items():
        print(f"{name}: {count}")
    print(f"포션: {player.potions}")
    print(f"골드: {player.gold}")


def show_equipment(player: Player) -> None:
    print("\n[장비]")
    print(f"무기 등급: +{player.weapon_level}")
    print(f"방어구 등급: +{player.armor_level}")
    print(f"무기 성향: {player.weapon_tag}")
    print(f"방어구 성향: {player.armor_tag}")


def shop_menu(player: Player) -> None:
    while True:
        print("\n[상점]")
        print("1) 포션 구매 (5 골드)")
        print("2) 재료 구매")
        print("3) 재료 판매 (개당 2 골드)")
        print("4) 나가기")
        choice = safe_int("> ", 1, 4)
        if choice == 1:
            buy_item(player, "포션")
        elif choice == 2:
            buy_materials(player)
        elif choice == 3:
            sell_materials(player)
        else:
            break


def buy_item(player: Player, item: str) -> None:
    cost = ITEM_SHOP_PRICES[item]
    if player.gold < cost:
        print("골드가 부족합니다.")
        return
    player.gold -= cost
    player.potions += 1
    print("포션을 구매했습니다.")


def buy_materials(player: Player) -> None:
    print("\n구매할 재료를 선택하세요.")
    print("1) 철 (4 골드)")
    print("2) 가죽 (3 골드)")
    print("3) 약초 (2 골드)")
    print("4) 취소")
    choice = safe_int("> ", 1, 4)
    if choice == 4:
        return
    material = ["철", "가죽", "약초"][choice - 1]
    cost = ITEM_SHOP_PRICES[material]
    if player.gold < cost:
        print("골드가 부족합니다.")
        return
    player.gold -= cost
    player.materials[material] += 1
    print(f"{material}을(를) 구매했습니다.")


def sell_materials(player: Player) -> None:
    print("\n판매할 재료를 선택하세요.")
    print("1) 철")
    print("2) 가죽")
    print("3) 약초")
    print("4) 취소")
    choice = safe_int("> ", 1, 4)
    if choice == 4:
        return
    material = ["철", "가죽", "약초"][choice - 1]
    if player.materials[material] <= 0:
        print("재료가 부족합니다.")
        return
    player.materials[material] -= 1
    player.gold += MATERIAL_SELL_PRICE
    print(f"{material}을(를) 판매했습니다.")


def merchant_event(player: Player, logbook: LogBook) -> None:
    log_print(logbook, "탐험 중 상인을 만났습니다.")
    log_print(logbook, "낡은 수레가 덜컹이며 멈춘다.")
    while True:
        print("1) 구매 2) 판매 3) 나가기")
        choice = safe_int("> ", 1, 3)
        if choice == 1:
            buy_materials(player)
        elif choice == 2:
            sell_materials(player)
        else:
            break


def blacksmith_event(player: Player, logbook: LogBook) -> None:
    log_print(logbook, "희귀한 대장장이를 만났습니다!")
    log_print(logbook, "쇳불이 튀고 망치 소리가 울린다.")
    print("1) 무기 강화 (철 2, 가죽 1)")
    print("2) 방어구 강화 (철 1, 가죽 2)")
    print("3) 무기 성향 변경")
    print("4) 방어구 성향 변경")
    print("5) 나가기")
    choice = safe_int("> ", 1, 5)
    if choice == 1:
        craft_equipment(player, "무기 강화")
    elif choice == 2:
        craft_equipment(player, "방어구 강화")
    elif choice == 3:
        choose_build_tag(player, "weapon")
    elif choice == 4:
        choose_build_tag(player, "armor")


def craft_equipment(player: Player, recipe_name: str) -> None:
    recipe = BLACKSMITH_RECIPES[recipe_name]
    if any(player.materials[name] < count for name, count in recipe.items()):
        print("재료가 부족합니다.")
        return
    for name, count in recipe.items():
        player.materials[name] -= count
    if recipe_name == "무기 강화":
        player.weapon_level += 1
    else:
        player.armor_level += 1
    print(f"{recipe_name} 완료! 장비가 강화되었습니다.")


def choose_build_tag(player: Player, slot: str) -> None:
    print("\n장비 성향을 선택하세요.")
    for index, tag in enumerate(BUILD_TAGS, start=1):
        print(f"{index}) {tag}")
    choice = safe_int("> ", 1, len(BUILD_TAGS))
    tag = BUILD_TAGS[choice - 1]
    if slot == "weapon":
        player.weapon_tag = tag
        print(f"무기 성향이 {tag}(으)로 설정되었습니다.")
    else:
        player.armor_tag = tag
        print(f"방어구 성향이 {tag}(으)로 설정되었습니다.")


def rest(player: Player) -> None:
    print("여관에서 휴식을 취합니다.")
    player.hp = player.max_hp
    print("체력이 모두 회복되었습니다.")


def town_menu(
    player: Player,
    logbook: LogBook,
    quest_manager: QuestManager,
    achievement_manager: AchievementManager,
) -> None:
    while True:
        print("\n[마을]")
        print("1) 상점")
        print("2) 인벤토리")
        print("3) 장비")
        print("4) 휴식")
        print("5) 탐험 출발")
        print("6) 상태")
        print("7) 로그 리플레이")
        print("8) 저장")
        print("9) 불러오기")
        print("10) 종료")
        choice = safe_int("> ", 1, 10)
        if choice == 1:
            shop_menu(player)
        elif choice == 2:
            show_inventory(player)
        elif choice == 3:
            show_equipment(player)
        elif choice == 4:
            rest(player)
        elif choice == 5:
            from systems.explore import exploration

            exploration(player, logbook)
            quest_manager.process(logbook, player)
            achievement_manager.process(logbook)
            if player.hp <= 0:
                print("쓰러졌습니다. 게임 오버.")
                break
        elif choice == 6:
            show_status(player)
        elif choice == 7:
            replay_logs(logbook)
        elif choice == 8:
            save_game(player, achievement_manager, logbook)
        elif choice == 9:
            if load_game(player, achievement_manager, logbook):
                quest_manager.active_quests = []
                quest_manager.activate_run_quests(logbook)
        else:
            print("게임을 종료합니다.")
            break


def replay_logs(logbook: LogBook) -> None:
    if not logbook.has_entries():
        print("로그가 없습니다.")
        return
    print("\n[로그 리플레이]")
    for line in logbook.replay():
        print(line)


def next_level_exp(level: int) -> int:
    return 10 + (level - 1) * 6
