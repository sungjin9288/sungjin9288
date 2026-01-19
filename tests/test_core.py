import asyncio
import random
import unittest

from models import Enemy, Player
from systems import explore
from utils.logging import LogBook


class TestCoreSystems(unittest.TestCase):
    def test_logbook_replay_order(self) -> None:
        logbook = LogBook()
        logbook.add("첫 줄")
        logbook.add("둘째 줄")
        self.assertEqual(list(logbook.replay()), ["첫 줄", "둘째 줄"])

    def test_next_level_exp_formula(self) -> None:
        self.assertEqual(explore.next_level_exp(1), 10)
        self.assertEqual(explore.next_level_exp(2), 16)

    def test_apply_level_up_increases_stats(self) -> None:
        player = Player(name="테스트")
        player.exp = 21
        logbook = LogBook()
        explore.apply_level_up(player, logbook)
        self.assertEqual(player.level, 2)
        self.assertEqual(player.max_hp, 24)
        self.assertEqual(player.hp, player.max_hp)
        self.assertEqual(player.atk, 5)
        self.assertEqual(player.defense, 2)
        self.assertEqual(player.exp, 11)

    def test_roll_drops_seeded(self) -> None:
        region = list(explore.REGION_DROPS.keys())[0]
        random.seed(3)
        drops = asyncio.run(explore.roll_drops(region))
        expected = [explore.REGION_DROPS[region][0][0]]
        self.assertEqual(drops, expected)

    def test_reward_multiplier_depth(self) -> None:
        region = "초원"
        self.assertEqual(explore.reward_multiplier(region, 1), 1.0)
        self.assertEqual(explore.reward_multiplier(region, 2), 1.1)

    def test_boss_entry_allowed(self) -> None:
        player = Player(name="테스트")
        player.level = explore.BOSS_ENTRY_LEVEL
        player.weapon_level = explore.BOSS_ENTRY_GEAR
        player.armor_level = explore.BOSS_ENTRY_GEAR
        allowed, _ = explore.can_enter_boss(player)
        self.assertTrue(allowed)

    def test_boss_entry_denied(self) -> None:
        player = Player(name="테스트")
        player.level = explore.BOSS_ENTRY_LEVEL - 1
        player.weapon_level = explore.BOSS_ENTRY_GEAR
        player.armor_level = explore.BOSS_ENTRY_GEAR
        player.potions = explore.BOSS_ENTRY_POTIONS
        allowed, _ = explore.can_enter_boss(player)
        self.assertFalse(allowed)

    def test_depth_multiplier_values(self) -> None:
        region = "초원"
        self.assertEqual(explore.reward_multiplier(region, 1), 1.0)
        self.assertEqual(explore.reward_multiplier(region, 2), 1.1)
        self.assertEqual(explore.reward_multiplier(region, 5), 1.4)

    def test_bonus_drop_trigger_rule(self) -> None:
        self.assertFalse(explore.bonus_drop_allowed("초원", 1))
        self.assertTrue(explore.bonus_drop_allowed("초원", 2))
        self.assertFalse(explore.bonus_drop_allowed("폐허 심층", 3))

    def test_boss_ending_logged(self) -> None:
        logbook = LogBook()
        explore.boss_ending(logbook)
        lines = list(logbook.replay())
        self.assertEqual(sum("엔딩:" in line for line in lines), 1)

    def test_resolve_explore_turn_returns(self) -> None:
        random.seed(2)
        enemy, drops, event = asyncio.run(explore.resolve_explore_turn("초원"))
        self.assertIn(event, {"merchant", "blacksmith", "none"})
        self.assertIsInstance(drops, list)
        self.assertTrue(enemy is None or isinstance(enemy, Enemy))


if __name__ == "__main__":
    unittest.main()
