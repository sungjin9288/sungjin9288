from typing import Iterable, Iterator


def prompt_int(prompt: str, min_value: int, max_value: int) -> int:
    while True:
        try:
            raw = input(prompt)
            value = int(raw)
            if min_value <= value <= max_value:
                return value
            print(f"{min_value}부터 {max_value} 사이의 숫자를 입력하세요.")
        except ValueError:
            print("잘못된 입력입니다. 숫자를 입력하세요.")


def event_generator(events: Iterable[str]) -> Iterator[str]:
    for event in events:
        yield event
