# 친구방 · 주파수 (chiring)

팀 프로토타입에 붙이는 **친구방(Lucky Talk·Lucky Moments·스토리)**, **주파수(기운 선물)**, **받은 주파수 듣기** 화면이에요.

- 이 폴더는 빌드된 결과물이라 그대로 올리면 `…/naver-1020-luck/chiring/` 주소로 열려요.
- 원본 코드(React + Vite): https://github.com/unahynn/chiring
- 따로 보기: https://unahynn.github.io/chiring/

수정은 원본 저장소에서 하고, `npx vite build --base ./` 결과물을 이 폴더에 다시 덮어쓰면 돼요.

## 팀 프로토타입에 붙이면서 바꾼 점 (2곳, `assets/index-*.js`)
- 주소 끝 `#frequency` / `#friends` / `#myluck`으로 시작 탭을 정할 수 있게 함 (팀 프로토타입의 주파수 탭 → `chiring/index.html#frequency`)
- 하단 내비 **홈·친구방** → 팀 프로토타입의 홈·친구방으로 (팀 프로토타입 안에 띄워져 있으면 postMessage `chiring:home` / `chiring:friends`, 단독으로 열면 `../index.html#home`)
원본 저장소에서 다시 빌드할 때 이 두 가지를 원본 코드(App의 첫 탭 상태, BottomNav onChange)에도 넣어 주세요.
- 주소 끝 `#moment-unahynn` 처럼 쓰면 그 친구의 스토리 화면으로 바로 시작, 스토리의 뒤로가기 → 팀 프로토타입 친구방 (팀 프로토타입 친구방의 Lucky Moments 카드에서 연결)
