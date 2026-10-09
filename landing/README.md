# 넥스트 스테이지 랜딩 템플릿

`reference/asan-startup`에서 뽑은 스타일(스케일 시스템, 컬러 토큰, 섹션 패턴)로 만든 랜딩 페이지입니다.
행사명, 팀, 파트너는 모두 **가상의 예시 콘텐츠**입니다.

빌드 없이 `index.html`을 브라우저로 열면 됩니다.

## 바꾸는 곳

| 바꿀 것 | 위치 |
|---|---|
| 브랜드 컬러, 폰트 | `style.css` 맨 위 `:root` (`--ink`, `--key-1`~`--key-4`) |
| 행사명, 일시, 소개 문구, 인용문, 푸터 | `index.html` |
| 프로그램·팀, 혜택, FAQ, 연혁 | `main.js` 맨 위 `PROGRAMS` / `PERKS` / `FAQ` / `HERITAGE` |
| 카드 이미지 | 지금은 `art()`가 만든 추상 그래픽. 실제 사진은 `.about__art`, `.team__art`, `.heritage__slide`의 `background`를 `url(...)`로 바꾸면 됨 |

## 섹션

GNB(스크롤하면 블러 배경) → Hero(키 컬러 캔버스 애니메이션) → About 카드 → Film(스크롤하면 박스 확대) →
Startups(컬러 탭, 응원하기) → Perks(로고 누르면 패널 전환) → FAQ(탭 + 아코디언) →
Quote(문장 사이에 컬러 창이 열림) → Heritage(스크롤 고정 타임라인) → 그라디언트 푸터.
Floating CTA와 링크 복사 토스트가 함께 들어 있습니다.

크기는 모두 `calc(시안 px * var(--s))`로 씁니다. 데스크톱은 1920px 시안, 모바일(1024px 미만)은 400px 시안 기준입니다.
