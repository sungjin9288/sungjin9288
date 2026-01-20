import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set

from utils.logging import LogBook, log_print


@dataclass
class Achievement:
    achievement_id: str
    description: str


ACHIEVEMENT_DEFS: List[Achievement] = [
    Achievement("first_boss_clear", "첫 보스 처치"),
    Achievement("bleed_kill", "출혈로 마무리"),
    Achievement("stun_block_charge", "기절로 차징 차단"),
    Achievement("first_craft", "첫 제작 성공"),
    Achievement("true_ending_clear", "진엔딩 처치"),
]


class AchievementManager:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.unlocked: Set[str] = set()
        self.last_log_index = 0
        self._load()

    def process(self, logbook: LogBook) -> None:
        new_lines = logbook.entries[self.last_log_index :]
        bleed_seen = False
        charge_seen = False
        for line in new_lines:
            if "출혈로" in line:
                bleed_seen = True
            if "힘을 모으기 시작합니다" in line:
                charge_seen = True
            if "제작 완료:" in line:
                self.unlock("first_craft", logbook)
            if "기절해 움직이지 못합니다" in line and charge_seen:
                self.unlock("stun_block_charge", logbook)
            if "전투 승리!" in line and bleed_seen:
                self.unlock("bleed_kill", logbook)
                bleed_seen = False
            if "폐허의 왕을 쓰러뜨렸습니다" in line:
                self.unlock("first_boss_clear", logbook)
            if "TRUE_ENDING_CLEAR" in line:
                self.unlock("true_ending_clear", logbook)
        self.last_log_index = len(logbook.entries)

    def unlock(self, achievement_id: str, logbook: LogBook) -> None:
        if achievement_id in self.unlocked:
            return
        self.unlocked.add(achievement_id)
        log_print(logbook, f"업적 달성: {self._get_description(achievement_id)}")
        self._save()

    def _get_description(self, achievement_id: str) -> str:
        for achievement in ACHIEVEMENT_DEFS:
            if achievement.achievement_id == achievement_id:
                return achievement.description
        return achievement_id

    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                self.unlocked = set(str(item) for item in data)
        except json.JSONDecodeError:
            self.unlocked = set()

    def _save(self) -> None:
        self.storage_path.write_text(
            json.dumps(sorted(self.unlocked), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def save(self) -> None:
        self._save()

    def set_unlocked(self, unlocked: List[str]) -> None:
        self.unlocked = set(unlocked)
