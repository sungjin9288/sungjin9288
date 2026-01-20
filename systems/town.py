
import random
from typing import List, Sequence

from models import (
    BLACKSMITH_RECIPES,
    BOSS_MATERIALS,
    BUILD_TAGS,
    CRAFT_RECIPES,
    EQUIPMENT_ITEMS,
    EQUIPMENT_TIERS,
    Player,
)
from systems.achievements import AchievementManager
from systems.dex import (
    DexManager,
    apply_equipment_completion_reward,
    apply_material_completion_reward,
    build_equipment_catalog,
    build_material_catalog,
    build_monster_catalog,
)
from systems.shop import (
    BASE_EQUIPMENT_STOCK,
    build_rotating_stock,
    get_buy_price,
    get_sell_price,
    merge_stock,
)
from systems.quests import QuestManager
from systems.crafting import can_craft, craft_item, get_equipment, list_all_recipes
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
    print(f"특수 무기: {player.weapon_item or '없음'}")
    print(f"특수 방어구: {player.armor_item or '없음'}")


def show_dex(player: Player, dex_manager: DexManager, logbook: LogBook) -> None:
    materials = list(build_material_catalog(player))
    equipment = list(build_equipment_catalog())
    monsters = list(build_monster_catalog())
    print("\n[도감]")
    print(f"재료 도감: {len(dex_manager.materials)}/{len(materials)}")
    for name in materials:
        status = "발견" if name in dex_manager.materials else "미발견"
        print(f"- {name}: {status}")
    print(f"\n장비 도감: {len(dex_manager.equipment)}/{len(equipment)}")
    for name in equipment:
        status = "발견" if name in dex_manager.equipment else "미발견"
        print(f"- {name}: {status}")
    print(f"\n몬스터 도감: {len(dex_manager.monsters)}/{len(monsters)}")
    for name in monsters:
        status = "발견" if name in dex_manager.monsters else "미발견"
        print(f"- {name}: {status}")
    true_ending = "달성" if "TRUE_ENDING_CLEAR" in logbook.entries else "미달성"
    print(f"\n진엔딩 기록: {true_ending}")


def shop_menu(player: Player, logbook: LogBook, rotating_stock: Sequence[str]) -> None:
    while True:
        print("\n[상점]")
        print(f"1) 포션 구매 ({get_buy_price('포션')} 골드)")
        print("2) 재료 구매")
        print(f"3) 재료 판매 (개당 {get_sell_price('약초')} 골드)")
        print("4) 장비 구매")
        print("5) 장비 판매")
        print("6) 나가기")
        choice = safe_int("> ", 1, 6)
        if choice == 1:
            buy_item(player, "포션")
        elif choice == 2:
            buy_materials(player, logbook)
        elif choice == 3:
            sell_materials(player)
        elif choice == 4:
            buy_equipment(player, logbook, rotating_stock)
        elif choice == 5:
            sell_equipment(player)
        else:
            break


def buy_item(player: Player, item: str) -> None:
    cost = get_buy_price(item)
    if player.gold < cost:
        print("골드가 부족합니다.")
        return
    player.gold -= cost
    player.potions += 1
    print("포션을 구매했습니다.")


def buy_materials(player: Player, logbook: LogBook) -> None:
    materials = list_materials_for_shop()
    print("\n구매할 재료를 선택하세요.")
    for index, name in enumerate(materials, start=1):
        print(f"{index}) {name} ({get_buy_price(name)} 골드)")
    print(f"{len(materials) + 1}) 취소")
    choice = safe_int("> ", 1, len(materials) + 1)
    if choice == len(materials) + 1:
        return
    material = materials[choice - 1]
    cost = get_buy_price(material)
    if player.gold < cost:
        print("골드가 부족합니다.")
        return
    player.gold -= cost
    player.materials[material] += 1
    print(f"{material}을(를) 구매했습니다.")
    logbook.add(f"DISCOVER_MATERIAL:{material}")


def sell_materials(player: Player) -> None:
    materials = list_materials_for_shop()
    print("\n판매할 재료를 선택하세요.")
    for index, name in enumerate(materials, start=1):
        print(f"{index}) {name}")
    print(f"{len(materials) + 1}) 취소")
    choice = safe_int("> ", 1, len(materials) + 1)
    if choice == len(materials) + 1:
        return
    material = materials[choice - 1]
    if player.materials[material] <= 0:
        print("재료가 부족합니다.")
        return
    player.materials[material] -= 1
    player.gold += get_sell_price(material)
    print(f"{material}을(를) 판매했습니다.")


def merchant_event(player: Player, logbook: LogBook) -> None:
    log_print(logbook, "탐험 중 상인을 만났습니다.")
    log_print(logbook, "낡은 수레가 덜컹이며 멈춘다.")
    while True:
        print("1) 구매 2) 판매 3) 나가기")
        choice = safe_int("> ", 1, 3)
        if choice == 1:
            buy_materials(player, logbook)
        elif choice == 2:
            sell_materials(player)
        else:
            break


def blacksmith_event(player: Player, logbook: LogBook) -> None:
    log_print(logbook, "희귀한 대장장이를 만났습니다!")
    log_print(logbook, "쇳불이 튀고 망치 소리가 울린다.")
    visit_count = sum(1 for line in logbook.entries if line == "BLACKSMITH_VISIT")
    if visit_count == 0:
        log_print(logbook, "처음 보는 얼굴이군. 이 불꽃은 오래 남는다.")
    elif visit_count == 2:
        log_print(logbook, "또 왔군. 네가 지나온 길이 망치에 남아 있다.")
    logbook.add("BLACKSMITH_VISIT")
    print("1) 무기 성향 변경")
    print("2) 방어구 성향 변경")
    print("3) 특수 장비 제작")
    print("4) 장비 착용")
    print("5) 나가기")
    choice = safe_int("> ", 1, 5)
    if choice == 1:
        choose_build_tag(player, "weapon")
    elif choice == 2:
        choose_build_tag(player, "armor")
    elif choice == 3:
        craft_special_item(player, logbook)
    elif choice == 4:
        equip_special_item(player)


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


def list_materials_for_shop() -> List[str]:
    return [
        "약초",
        "야생꽃",
        "사슴뿔",
        "이끼씨앗",
        "은빛꽃잎",
        "철",
        "수정",
        "박쥐날개",
        "광휘석",
        "어둠버섯",
        "고철",
        "망령가루",
        "낡은 인장",
        "망각의 유물",
        "저주의 조각",
    ]


def buy_equipment(player: Player, logbook: LogBook, rotating_stock: Sequence[str]) -> None:
    items = merge_stock(BASE_EQUIPMENT_STOCK, rotating_stock)
    print("\n구매할 장비를 선택하세요.")
    for index, name in enumerate(items, start=1):
        item = EQUIPMENT_ITEMS[name]
        print(f"{index}) {item.name} +ATK {item.atk} +DEF {item.defense} +EXP {item.explore} ({get_buy_price(name)} 골드)")
    print(f"{len(items) + 1}) 취소")
    choice = safe_int("> ", 1, len(items) + 1)
    if choice == len(items) + 1:
        return
    selected = items[choice - 1]
    price = get_buy_price(selected)
    if player.gold < price:
        print("골드가 부족합니다.")
        return
    player.gold -= price
    item = EQUIPMENT_ITEMS[selected]
    if item.slot == "weapon":
        player.weapons_owned.append(item.name)
    else:
        player.armors_owned.append(item.name)
    print(f"{item.name}을(를) 구매했습니다.")
    logbook.add(f"DISCOVER_EQUIP:{item.name}")


def sell_equipment(player: Player) -> None:
    owned_items = [("weapon", name) for name in player.weapons_owned] + [
        ("armor", name) for name in player.armors_owned
    ]
    if not owned_items:
        print("판매할 장비가 없습니다.")
        return
    print("\n판매할 장비를 선택하세요.")
    for index, (_, name) in enumerate(owned_items, start=1):
        item = get_equipment(name)
        price = get_sell_price(name)
        print(f"{index}) {item.name} +ATK {item.atk} +DEF {item.defense} +EXP {item.explore} ({price} 골드)")
    print(f"{len(owned_items) + 1}) 취소")
    choice = safe_int("> ", 1, len(owned_items) + 1)
    if choice == len(owned_items) + 1:
        return
    slot, selected = owned_items[choice - 1]
    price = get_sell_price(selected)
    equipped = False
    if slot == "weapon" and player.weapon_item == selected:
        equipped = True
    if slot == "armor" and player.armor_item == selected:
        equipped = True
    print("\n[판매 확인]")
    print(f"장비: {selected}")
    print(f"판매가: {price} 골드")
    if equipped:
        print("장착 중인 장비입니다. 판매 시 자동 해제됩니다.")
    print(f"골드: {player.gold} -> {player.gold + price}")
    print("1) 판매 2) 취소")
    confirm = safe_int("> ", 1, 2)
    if confirm == 2:
        return
    if slot == "weapon":
        player.weapons_owned.remove(selected)
        if player.weapon_item == selected:
            player.weapon_item = ""
    else:
        player.armors_owned.remove(selected)
        if player.armor_item == selected:
            player.armor_item = ""
    player.gold += price
    print(f"{selected}을(를) 판매했습니다.")


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


def craft_special_item(player: Player, logbook: LogBook) -> None:
    recipes = list_all_recipes()
    if not recipes:
        print("제작할 수 있는 장비가 없습니다.")
        return
    print("\n제작 장비 목록:")
    for index, name in enumerate(recipes, start=1):
        item = get_equipment(name)
        recipe = CRAFT_RECIPES[name]
        materials = ", ".join(f"{mat}x{count}" for mat, count in recipe.items())
        status = "가능" if can_craft(player.materials, recipe) else "재료 부족"
        print(
            f"{index}) {item.name} [{item.slot}] +ATK {item.atk} +DEF {item.defense} +EXP {item.explore} ({materials}) [{status}]"
        )
        if item.description:
            print(f"   {item.description}")
    print(f"{len(recipes) + 1}) 취소")
    choice = safe_int("> ", 1, len(recipes) + 1)
    if choice == len(recipes) + 1:
        return
    selected = recipes[choice - 1]
    recipe = CRAFT_RECIPES[selected]
    if any(material in BOSS_MATERIALS for material in recipe):
        if "BLACKSMITH_BOSS_MATERIAL" not in logbook.entries:
            log_print(logbook, "보스의 잔재로구나. 이 불꽃이 달라진다.")
            logbook.add("BLACKSMITH_BOSS_MATERIAL")
    if not can_craft(player.materials, recipe):
        print("재료가 부족합니다.")
        return
    if craft_item(player, selected, logbook):
        if EQUIPMENT_TIERS.get(selected, 1) == 3:
            if "BLACKSMITH_TIER3_FORGE" not in logbook.entries:
                log_print(logbook, "이런 칼날은 두 번 만들지 않는다.")
                logbook.add("BLACKSMITH_TIER3_FORGE")


def equip_special_item(player: Player) -> None:
    print("\n장비 슬롯을 선택하세요.")
    print("1) 무기")
    print("2) 방어구")
    print("3) 취소")
    slot_choice = safe_int("> ", 1, 3)
    if slot_choice == 3:
        return
    if slot_choice == 1:
        items = player.weapons_owned
        slot_name = "무기"
    else:
        items = player.armors_owned
        slot_name = "방어구"
    if not items:
        print("착용할 장비가 없습니다.")
        return
    print(f"\n{slot_name} 목록:")
    for index, name in enumerate(items, start=1):
        item = get_equipment(name)
        print(f"{index}) {item.name} +ATK {item.atk} +DEF {item.defense} +EXP {item.explore}")
    choice = safe_int("> ", 1, len(items))
    selected = items[choice - 1]
    if slot_choice == 1:
        player.weapon_item = selected
    else:
        player.armor_item = selected
    print(f"{slot_name}을(를) {selected}(으)로 착용했습니다.")


def rest(player: Player) -> None:
    print("여관에서 휴식을 취합니다.")
    player.hp = player.max_hp
    print("체력이 모두 회복되었습니다.")


def town_menu(
    player: Player,
    logbook: LogBook,
    quest_manager: QuestManager,
    achievement_manager: AchievementManager,
    dex_manager: DexManager,
) -> None:
    rng = random.Random()
    rotating_stock = build_rotating_stock(rng, BASE_EQUIPMENT_STOCK)
    while True:
        print("\n[마을]")
        print("1) 상점")
        print("2) 인벤토리")
        print("3) 장비")
        print("4) 휴식")
        print("5) 탐험 출발")
        print("6) 상태")
        print("7) 도감 보기")
        print("8) 로그 리플레이")
        print("9) 저장")
        print("10) 불러오기")
        print("11) 종료")
        choice = safe_int("> ", 1, 11)
        if choice == 1:
            shop_menu(player, logbook, rotating_stock)
            dex_manager.process(logbook)
            apply_material_completion_reward(player, dex_manager, logbook)
            apply_equipment_completion_reward(player, dex_manager, logbook)
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
            dex_manager.process(logbook)
            apply_material_completion_reward(player, dex_manager, logbook)
            apply_equipment_completion_reward(player, dex_manager, logbook)
            rotating_stock = build_rotating_stock(
                rng, BASE_EQUIPMENT_STOCK, rotating_stock
            )
            if player.hp <= 0:
                print("쓰러졌습니다. 게임 오버.")
                break
        elif choice == 6:
            show_status(player)
        elif choice == 7:
            show_dex(player, dex_manager, logbook)
        elif choice == 8:
            replay_logs(logbook)
        elif choice == 9:
            save_game(player, achievement_manager, dex_manager, logbook)
        elif choice == 10:
            if load_game(player, achievement_manager, dex_manager, logbook):
                quest_manager.active_quests = []
                quest_manager.activate_run_quests(logbook)
                apply_material_completion_reward(player, dex_manager, logbook)
                apply_equipment_completion_reward(player, dex_manager, logbook)
                rotating_stock = build_rotating_stock(
                    rng, BASE_EQUIPMENT_STOCK, rotating_stock
                )
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
