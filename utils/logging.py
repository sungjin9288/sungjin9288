from typing import Iterator, List


class LogBook:
    def __init__(self) -> None:
        self.entries: List[str] = []

    def add(self, line: str) -> None:
        self.entries.append(line)

    def extend(self, lines: List[str]) -> None:
        self.entries.extend(lines)

    def replay(self) -> Iterator[str]:
        for line in self.entries:
            if line.startswith(("DISCOVER_", "KILL_BOSS:", "TRUE_ENDING_")):
                continue
            yield line

    def has_entries(self) -> bool:
        return bool(self.entries)


def log_print(logbook: LogBook, line: str) -> None:
    print(line)
    logbook.add(line)
