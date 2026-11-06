# Damage Collector

적을 때려 나온 데미지 숫자를 모아 다시 던지는 2D 액션 게임입니다.
Python과 pico2d로 개발할 예정입니다.

## 프로젝트 자료

- [1차 발표 PPT](docs/presentations/데미지_콜렉터_1차발표.pptx)
- [게임 기획 PPT](docs/presentations/데미지_콜렉터_기획서.pptx)

## 폴더 구성

- `src/`: 게임 코드
- `assets/`: 이미지와 사운드
- `tests/`: 테스트 코드
- `docs/presentations/`: 발표 및 기획 자료

## 개발 상태

주인공의 좌우 이동과 4프레임 걷기·단검 공격 애니메이션을 구현했습니다. 공격은 현재 모션만 재생합니다.

## 실행 방법

저장소 폴더에서 실행합니다.

```powershell
python -m pip install -r requirements.txt
python src/main.py
```

- `←`, `→`: 이동. 양쪽을 함께 누르면 멈추고, 한쪽을 놓으면 남은 방향으로 이동합니다.
- `X`: 바라보는 방향으로 단검을 휘두릅니다. 공격하는 0.4초 동안 이동을 멈춥니다.
- `Esc`: 종료
- 화면: 1280×720, 주인공 이미지 높이: 96픽셀, 이동 속도: 초당 260픽셀
- `src/player.py`의 `height`, `speed`로 크기와 속도를 조절합니다.
- 배경과 주인공 이미지는 AI 생성 시안을 사용합니다.
