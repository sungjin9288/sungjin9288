import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from models import Player
from utils.logging import LogBook, log_print


@dataclass
class Quest:
    quest_id: str
    description: str
    key: str
    target: int
    progress: int = 0
    completed: bool = False
    reward_gold: int = 0
    reward_material: Optional[Tuple[str, int]] = None
    reward_log: Optional[str] = None


QUEST_POOL: List[Quest] = [
    Quest("victory_2", "전투 2회 승리", "victory", 2, reward_gold=5),
    Quest("materials_3", "재료 3개 획득", "material", 3, reward_material=("철", 1)),
    Quest("meet_merchant", "상인 만나기", "merchant", 1, reward_log="상인의 호의를 얻었다."),
]


class QuestManager:
    def __init__(self, quests: Optional[List[Quest]] = None) -> None:
        self.active_quests: List[Quest] = quests or []
        self.last_log_index = 0

    def activate_run_quests(self, logbook: LogBook) -> None:
        if self.active_quests:
            return
        count = min(3, len(QUEST_POOL))
        self.active_quests = [self._clone(quest) for quest in random.sample(QUEST_POOL, count)]
        for quest in self.active_quests:
            log_print(logbook, f"퀘스트 활성화: {quest.description}")

    def process(self, logbook: LogBook, player: Player) -> None:
        new_lines = logbook.entries[self.last_log_index :]
        counters = self._count_events(new_lines)
        for quest in self.active_quests:
            if quest.completed:
                continue
            quest.progress = min(quest.target, quest.progress + counters.get(quest.key, 0))
            if quest.progress >= quest.target:
                quest.completed = True
                self._apply_reward(quest, player, logbook)
        self.last_log_index = len(logbook.entries)

    def _apply_reward(self, quest: Quest, player: Player, logbook: LogBook) -> None:
        log_print(logbook, f"퀘스트 완료: {quest.description}")
        if quest.reward_gold:
            player.gold += quest.reward_gold
            log_print(logbook, f"보상: 골드 {quest.reward_gold}")
        if quest.reward_material:
            name, count = quest.reward_material
            player.materials[name] += count
            log_print(logbook, f"보상: {name} {count}개")
        if quest.reward_log:
            log_print(logbook, quest.reward_log)

    def _count_events(self, lines: List[str]) -> Dict[str, int]:
        counters = {"victory": 0, "material": 0, "merchant": 0}
        for line in lines:
            if "전투 승리!" in line:
                counters["victory"] += 1
            if "재료 획득:" in line:
                counters["material"] += 1
            if "상인을 만났습니다" in line:
                counters["merchant"] += 1
        return counters

    def _clone(self, quest: Quest) -> Quest:
        return Quest(
            quest_id=quest.quest_id,
            description=quest.description,
            key=quest.key,
            target=quest.target,
            reward_gold=quest.reward_gold,
            reward_material=quest.reward_material,
            reward_log=quest.reward_log,
        )
