import asyncio
import random
import tempfile
import unittest
from pathlib import Path

from models import (
    BOSS_MATERIALS,
    BUILD_TAGS,
    CRAFT_RECIPES,
    EQUIPMENT_ITEMS,
    EQUIPMENT_TIERS,
    Enemy,
    Player,
    get_equipment_bonus,
)
from systems import explore
from systems.achievements import AchievementManager
from systems.combat import (
    BOSS_NAME,
    apply_bleed_tick,
    apply_damage_reduction,
    calculate_stun_chance,
    is_boss_enraged,
    resolve_boss_intent,
)
from systems.crafting import craft_item, list_craftable
from systems.dex import DexManager
from systems.quests import Quest, QuestManager
from systems.save import load_game, save_game
from systems.shop import BASE_EQUIPMENT_STOCK, build_rotating_stock, get_sell_price
from utils.logging import LogBook


def first_region() -> str:
    return next(iter(explore.REGION_DROPS))


def boss_region() -> str:
    return "폐허 심층"


class TestCoreSystems(unittest.TestCase):
    def test_logbook_replay_order(self) -> None:
        logbook = LogBook()
        logbook.add("first")
        logbook.add("second")
        self.assertEqual(list(logbook.replay()), ["first", "second"])

    def test_next_level_exp_formula(self) -> None:
        self.assertEqual(explore.next_level_exp(1), 10)
        self.assertEqual(explore.next_level_exp(2), 16)

    def test_level_up_selection_attack(self) -> None:
        player = Player(name="tester")
        logbook = LogBook()
        explore.apply_level_up_selection(player, explore.LEVEL_UP_CHOICES[0], logbook)
        self.assertEqual(player.atk, 6)

    def test_level_up_selection_survival(self) -> None:
        player = Player(name="tester")
        logbook = LogBook()
        explore.apply_level_up_selection(player, explore.LEVEL_UP_CHOICES[1], logbook)
        self.assertEqual(player.defense, 2)
        self.assertEqual(player.max_hp, 25)
        self.assertEqual(player.hp, player.max_hp)

    def test_explore_bonus_multiplier(self) -> None:
        player = Player(name="tester")
        player.explore_bonus = 0.05
        region = first_region()
        value = explore.reward_multiplier(region, 1, player)
        self.assertAlmostEqual(value, 1.05)

    def test_equipment_tag_bonus(self) -> None:
        player = Player(name="tester")
        player.weapon_tag = "OFFENSE"
        player.armor_tag = "DEFENSE"
        atk_bonus, def_bonus, explore_bonus = get_equipment_bonus(player)
        self.assertEqual(atk_bonus, 1)
        self.assertEqual(def_bonus, 1)
        self.assertEqual(explore_bonus, 0.0)

    def test_boss_entry_allowed(self) -> None:
        player = Player(name="tester")
        player.level = explore.BOSS_ENTRY_LEVEL
        player.weapon_level = explore.BOSS_ENTRY_GEAR
        player.armor_level = explore.BOSS_ENTRY_GEAR
        allowed, _ = explore.can_enter_boss(player)
        self.assertTrue(allowed)

    def test_boss_entry_denied(self) -> None:
        player = Player(name="tester")
        player.level = explore.BOSS_ENTRY_LEVEL - 1
        player.weapon_level = explore.BOSS_ENTRY_GEAR
        player.armor_level = explore.BOSS_ENTRY_GEAR
        player.potions = explore.BOSS_ENTRY_POTIONS
        allowed, _ = explore.can_enter_boss(player)
        self.assertFalse(allowed)

    def test_bonus_drop_trigger_rule(self) -> None:
        region = first_region()
        self.assertFalse(explore.bonus_drop_allowed(region, 1))
        self.assertTrue(explore.bonus_drop_allowed(region, 2))
        self.assertFalse(explore.bonus_drop_allowed(boss_region(), 3))

    def test_boss_ending_logged(self) -> None:
        logbook = LogBook()
        player = Player(name="tester")
        explore.boss_ending(logbook, player)
        lines = list(logbook.replay())
        self.assertEqual(sum("엔딩:" in line for line in lines), 1)

    def test_resolve_explore_turn_returns(self) -> None:
        random.seed(2)
        region = first_region()
        enemy, drops, event = asyncio.run(explore.resolve_explore_turn(region, 0.0))
        self.assertIn(event, {"merchant", "blacksmith", "none"})
        self.assertIsInstance(drops, list)
        self.assertTrue(enemy is None or isinstance(enemy, Enemy))

    def test_boss_charge_to_heavy(self) -> None:
        self.assertEqual(resolve_boss_intent(False, 0.1), "charge")
        self.assertEqual(resolve_boss_intent(True, 0.9), "heavy")

    def test_guard_reduces_damage(self) -> None:
        reduced = apply_damage_reduction(10, False, True)
        self.assertLess(reduced, 10)

    def test_boss_enrage_threshold(self) -> None:
        self.assertFalse(is_boss_enraged(40, 100))
        self.assertTrue(is_boss_enraged(30, 100))

    def test_bleed_ticks_apply(self) -> None:
        hp, turns = apply_bleed_tick(10, 3)
        self.assertEqual(hp, 8)
        self.assertEqual(turns, 2)

    def test_boss_stun_resist(self) -> None:
        boss_chance = calculate_stun_chance(BOSS_NAME)
        normal_chance = calculate_stun_chance("slime")
        self.assertLess(boss_chance, normal_chance)

    def test_quest_completion(self) -> None:
        quest = Quest("victory_1", "전투 1회 승리", "victory", 1, reward_gold=3)
        quest_manager = QuestManager([quest])
        player = Player(name="tester")
        logbook = LogBook()
        logbook.add("전투 승리! 경험치 1, 골드 1 획득!")
        quest_manager.process(logbook, player)
        self.assertTrue(quest_manager.active_quests[0].completed)
        self.assertEqual(player.gold, 13)

    def test_achievement_unlocked_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_path = Path(tmp_dir) / "achievements.json"
            manager = AchievementManager(storage_path)
            logbook = LogBook()
            logbook.add("폐허의 왕을 쓰러뜨렸습니다. 새로운 엔딩이 열립니다.")
            manager.process(logbook)
            manager.process(logbook)
            self.assertEqual(len(manager.unlocked), 1)

    def test_quest_process_no_flow_impact(self) -> None:
        player = Player(name="tester")
        player.hp = 15
        player.exp = 7
        quest_manager = QuestManager([])
        logbook = LogBook()
        logbook.add("탐험을 시작합니다...")
        quest_manager.process(logbook, player)
        self.assertEqual(player.hp, 15)
        self.assertEqual(player.exp, 7)

    def test_save_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = Path(tmp_dir) / "savegame.json"
            ach_path = Path(tmp_dir) / "achievements.json"
            player = Player(name="tester")
            player.gold = 33
            player.materials["철"] = 2
            logbook = LogBook()
            achievements = AchievementManager(ach_path)
            dex_manager = DexManager()
            achievements.set_unlocked(["first_boss_clear"])
            achievements.save()
            save_game(player, achievements, dex_manager, logbook, save_path)
            player.gold = 1
            player.materials["철"] = 0
            achievements.set_unlocked([])
            load_game(player, achievements, dex_manager, logbook, save_path)
            self.assertEqual(player.gold, 33)
            self.assertEqual(player.materials["철"], 2)
            self.assertIn("first_boss_clear", achievements.unlocked)

    def test_load_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = Path(tmp_dir) / "missing.json"
            ach_path = Path(tmp_dir) / "achievements.json"
            player = Player(name="tester")
            logbook = LogBook()
            achievements = AchievementManager(ach_path)
            dex_manager = DexManager()
            result = load_game(player, achievements, dex_manager, logbook, save_path)
            self.assertFalse(result)

    def test_save_preserves_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = Path(tmp_dir) / "savegame.json"
            ach_path = Path(tmp_dir) / "achievements.json"
            player = Player(name="tester")
            player.materials["야생꽃"] = 3
            logbook = LogBook()
            achievements = AchievementManager(ach_path)
            dex_manager = DexManager()
            save_game(player, achievements, dex_manager, logbook, save_path)
            player.materials["야생꽃"] = 0
            load_game(player, achievements, dex_manager, logbook, save_path)
            self.assertEqual(player.materials["야생꽃"], 3)

    def test_craft_consumes_materials(self) -> None:
        player = Player(name="tester")
        player.materials["사슴뿔"] = 2
        player.materials["야생꽃"] = 1
        logbook = LogBook()
        result = craft_item(player, "초원의 결의검", logbook)
        self.assertTrue(result)
        self.assertEqual(player.materials["사슴뿔"], 0)
        self.assertIn("초원의 결의검", player.weapons_owned)

    def test_list_craftable(self) -> None:
        materials = {"약초": 2, "사슴뿔": 1}
        craftable = list_craftable(materials)
        self.assertIn("길잡이 활", craftable)

    def test_sell_price_listed_equipment(self) -> None:
        self.assertEqual(get_sell_price("초원의 결의검"), 6)

    def test_sell_price_recipe_equipment(self) -> None:
        self.assertEqual(get_sell_price("피의 전투도끼"), 4)

    def test_rotating_stock_has_all_builds(self) -> None:
        rng = random.Random(1)
        rotating = build_rotating_stock(rng, BASE_EQUIPMENT_STOCK)
        self.assertEqual(len(rotating), 3)
        for tag in BUILD_TAGS:
            self.assertTrue(any(EQUIPMENT_ITEMS[name].tag == tag for name in rotating))

    def test_rotating_stock_excludes_tier3(self) -> None:
        rng = random.Random(2)
        rotating = build_rotating_stock(rng, BASE_EQUIPMENT_STOCK)
        self.assertTrue(all(EQUIPMENT_TIERS[name] <= 2 for name in rotating))

    def test_rotating_stock_refresh_changes(self) -> None:
        rng = random.Random(3)
        first = build_rotating_stock(rng, BASE_EQUIPMENT_STOCK)
        second = build_rotating_stock(rng, BASE_EQUIPMENT_STOCK, first)
        self.assertNotEqual(first, second)

    def test_tier3_recipes_require_boss_material(self) -> None:
        tier3_items = [name for name, tier in EQUIPMENT_TIERS.items() if tier == 3]
        for item_name in tier3_items:
            recipe = CRAFT_RECIPES[item_name]
            self.assertTrue(any(mat in BOSS_MATERIALS for mat in recipe))

    def test_dex_material_discovery(self) -> None:
        logbook = LogBook()
        logbook.add("DISCOVER_MATERIAL:약초")
        dex_manager = DexManager()
        dex_manager.process(logbook)
        self.assertIn("약초", dex_manager.materials)

    def test_dex_equipment_discovery(self) -> None:
        player = Player(name="tester")
        player.materials["사슴뿔"] = 2
        player.materials["야생꽃"] = 1
        logbook = LogBook()
        craft_item(player, "초원의 결의검", logbook)
        dex_manager = DexManager()
        dex_manager.process(logbook)
        self.assertIn("초원의 결의검", dex_manager.equipment)

    def test_dex_persists_through_save(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = Path(tmp_dir) / "savegame.json"
            ach_path = Path(tmp_dir) / "achievements.json"
            player = Player(name="tester")
            logbook = LogBook()
            achievements = AchievementManager(ach_path)
            dex_manager = DexManager(materials=["약초"], equipment=["초원의 결의검"], monsters=["슬라임"])
            save_game(player, achievements, dex_manager, logbook, save_path)
            loaded_dex = DexManager()
            load_game(player, achievements, loaded_dex, logbook, save_path)
            self.assertIn("약초", loaded_dex.materials)
            self.assertIn("초원의 결의검", loaded_dex.equipment)
            self.assertIn("슬라임", loaded_dex.monsters)

    def test_new_material_in_region_drops(self) -> None:
        self.assertTrue(
            any(name == "이끼씨앗" for name, _ in explore.REGION_DROPS["초원"])
        )

    def test_new_equipment_in_recipes(self) -> None:
        self.assertIn("맹렬한 장창", EQUIPMENT_ITEMS)
        self.assertIn("맹렬한 장창", CRAFT_RECIPES)

    def test_conquest_bonus_rule(self) -> None:
        self.assertEqual(explore.REGION_CONQUEST_BONUS["초원"], ("초원의 정수", 0.15))
        self.assertEqual(explore.REGION_CONQUEST_BONUS["동굴"], ("심층 광석", 0.15))
        self.assertEqual(explore.REGION_CONQUEST_BONUS["폐허"], ("부패의 핵", 0.15))

    def test_bonus_materials_used_in_recipes(self) -> None:
        self.assertIn("초원의 정수", CRAFT_RECIPES["맹렬한 장창"])
        self.assertIn("심층 광석", CRAFT_RECIPES["수호자의 철퇴"])
        self.assertIn("부패의 핵", CRAFT_RECIPES["심연의 갑옷"])


if __name__ == "__main__":
    unittest.main()
