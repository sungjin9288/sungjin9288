from models import Player
from systems.town import town_menu
from utils.logging import LogBook


# 실행 예시(플레이 흐름)
# 마을 메뉴 선택
# 1) 상점
# 2) 인벤토리
# 3) 장비
# 4) 휴식
# 5) 탐험 출발
# 6) 상태
# 7) 로그 리플레이
# 8) 종료
# > 5
# 탐험을 시작합니다...
# 야생에서 고블린을 만났다!
# 1) 공격 2) 방어 3) 포션 4) 도망
# > 1
# 고블린에게 4 피해!
# 고블린의 공격! 2 피해를 받았다.
# 전투 승리! 경험치 6, 골드 4 획득!
# 재료 획득: 가죽 +1
# 탐험 중 상인을 만났습니다.
# 마을로 돌아갑니다...


def main() -> None:
    print("CLI 싱글플레이 RPG에 오신 것을 환영합니다.")
    name = input("영웅의 이름을 입력하세요: ").strip() or "영웅"
    player = Player(name=name)
    logbook = LogBook()
    town_menu(player, logbook)


if __name__ == "__main__":
    main()
