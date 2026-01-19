from typing import List


def safe_int(prompt: str, min_value: int, max_value: int) -> int:
    while True:
        try:
            raw = input(prompt).strip()
            value = int(raw)
            if min_value <= value <= max_value:
                return value
            print(f"{min_value}부터 {max_value} 사이의 숫자를 입력하세요.")
        except ValueError:
            print("잘못된 입력입니다. 숫자를 입력하세요.")


def clamp(value: int, min_value: int, max_value: int) -> int:
    return max(min_value, min(value, max_value))


def list_to_text(items: List[str]) -> str:
    return ", ".join(items) if items else "없음"
