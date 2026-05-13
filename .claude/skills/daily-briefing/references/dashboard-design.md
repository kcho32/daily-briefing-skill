# HTML 대시보드 디자인 가이드

**언제 읽나**: Step 9 (HTML 대시보드 작성) 진입 시. 매일 발행이므로 사실상 매일 1회.
**역할**: 모바일 친화 다크 테마의 일관된 디자인 적용. 색상 코딩과 레이아웃 표준 통일.

---

## 디자인 원칙

- **모바일 우선**: 좁은 화면(320~480px) 에서 잘 보이도록 표/카드 위주
- **다크 테마**: 새벽/심야 열람 가정
- **정보 밀도**: 한 화면에 핵심 7~10개 정도 노출. 불필요 장식 최소화
- **차트는 단순 SVG 또는 생략**: 외부 차트 라이브러리 의존 X

---

## CSS 변수 (스타일 통일)

```css
:root {
  --bg:         #0f1419;
  --card:       #161b22;
  --border:     #30363d;
  --text:       #e6e6e6;
  --text-muted: #8b949e;
  --accent:     #58a6ff;

  /* 의미별 색상 코드 */
  --green:  #56d364;  /* 상승, 긍정 */
  --red:    #f85149;  /* 하락, 위험 */
  --yellow: #e3b341;  /* 주의 */
  --gray:   #8b949e;  /* 중립 */
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', sans-serif;
  font-size: 14px;
  line-height: 1.5;
  padding: 12px;
}

.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}
```

---

## 모드별 상단 배너

대시보드 최상단에 모드에 맞는 배너:

| 모드 | 배경 | 텍스트 색 | 이모지 |
|------|------|---------|------|
| 위기 | `#5a1a1a` | `#ff7b72` | 🚨 |
| 액션 | `#1a3a5a` | `#58a6ff` | 🎯 |
| 리마인드 | `#5a4a1a` | `#e3b341` | ⚠️ |
| 안정 | `#1a4a2a` | `#56d364` | ✅ |

```html
<div class="banner banner-crisis">
  🚨 위기 시그널 — VIX 32, HY 스프레드 8.5%
</div>
```

```css
.banner {
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-weight: 600;
}
.banner-crisis   { background: #5a1a1a; color: #ff7b72; }
.banner-action   { background: #1a3a5a; color: #58a6ff; }
.banner-remind   { background: #5a4a1a; color: #e3b341; }
.banner-stable   { background: #1a4a2a; color: #56d364; }
```

---

## 표준 섹션 (순서 고정)

대시보드 카드는 다음 순서로 배치:

1. **헤더** (날짜, 모드 표시 배너)
2. **거시 환경**: 8개 지표 표 + 위기 트리거 평가
3. **역사 비교**: 한 줄 + 의미 설명
4. **포트폴리오 현황** (3개 하위 카드):
   - 4a. 미국 + 한국 분리 표
   - 4b. **상대성과 카드** — 포트폴리오 vs S&P500 / NDX / SOXX / KOSPI 일일 변동률 + 핵심 벤치마크 대비 ±x.x%p
   - 4c. **가드레일 카드** — 🔴 위험 / 🟠 경고 / 🟡 주의 단계별 표시 (없으면 ✅ 한 줄)
5. **추천 반영 추적**: ✅/⚠️ 목록
6. **보유 종목 분석**: 변동 ±3% 이상 종목 + **주요 보유 종목 주간 점검**(수요일 또는 비중 ≥10%) — 없으면 "특이사항 없음"
7. **매도/매수 추천**: 보유 종목 기준, 시세 앵커 트리거 가격 명시
8. **🆕 신규 매수 후보** (Top 3~5): 보유 외 매력적 종목 + **각 후보별 100점 점수표** + 보류 시 사유
9. **세금 시뮬레이션**: KIS + Kiwoom 합산, 공제 잔여, 예상 세금
10. **이번 달 입금 가이드**: 다음 입금 D-X, 분배 추천
11. **이번 주 일정**: FOMC, 어닝, 경제지표
12. **회고 카드 (조건부)** — 월요일이면 7일 회고 / 매월 1일이면 30일 회고. 적중률 + 평균 수익률 + 실패 카테고리 분포

---

## 표 (table) 표준

```html
<table class="data-table">
  <thead>
    <tr><th>종목</th><th>현재가</th><th>일변동</th><th>비중</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>[종목]</td>
      <td>$[현재가]</td>
      <td class="up">+[변동]%</td>
      <td>[비중]%</td>
    </tr>
  </tbody>
</table>
```

```css
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th, .data-table td { padding: 8px; border-bottom: 1px solid var(--border); text-align: left; }
.data-table th { color: var(--text-muted); font-weight: 600; }
.up   { color: var(--green); }
.down { color: var(--red); }
```

---

## 카드 + 배지 패턴 (신규 후보 노출용)

```html
<div class="card">
  <div class="card-title">
    [종목] <span class="badge badge-attract">매력 N/6</span>
  </div>
  <div class="card-body">
    현재가 $[값] · 목표가 $[값] (+[%]) · 비중 추천 [%]
    <br><span class="muted">🔻 리스크: [현재 상태 1줄]</span>
  </div>
</div>
```

```css
.badge { font-size: 11px; padding: 2px 8px; border-radius: 12px; }
.badge-attract { background: rgba(86, 211, 100, 0.15); color: var(--green); }
.badge-risk    { background: rgba(248, 81, 73, 0.15); color: var(--red); }
.badge-neutral { background: rgba(139, 148, 158, 0.15); color: var(--gray); }
.muted { color: var(--text-muted); font-size: 12px; }
```

---

## 시세 앵커 트리거 가격 표시 패턴

집중 위험 종목의 단계적 익절 트리거를 보여줄 때:

```html
<div class="trigger-card">
  <div class="trigger-symbol">[종목] <span class="muted">비중 [X]%</span></div>
  <table class="trigger-table">
    <tr><td>1차 익절</td><td class="up">$[값]</td><td class="muted">ma50 + 2×ATR</td></tr>
    <tr><td>2차 익절</td><td class="up">$[값]</td><td class="muted">52w high × 0.97</td></tr>
    <tr><td>손절</td><td class="down">$[값]</td><td class="muted">ma200 − 2×ATR</td></tr>
    <tr><td>현재가</td><td>$[값]</td><td class="muted">(stale: YYYY-MM-DD 캐시 — stale 시만)</td></tr>
  </table>
</div>
```

`anchors_source == "yfinance:stale"` 인 경우 마지막 행에 `(stale: YYYY-MM-DD 캐시)` 명시.

---

## 가드레일 카드 패턴 (4c)

3단계를 색상으로 구분. 같은 색 코드를 banner 와 일치.

```html
<div class="card">
  <div class="card-title">🛡️ 포트폴리오 가드레일</div>
  <div class="guardrail-row guardrail-danger">🔴 위험: [항목] [값] ([어느 한도 초과]) · D+[N]</div>
  <div class="guardrail-row guardrail-warn">🟠 경고: [항목] [값]</div>
  <div class="guardrail-row guardrail-caution">🟡 주의: [항목] [값] ([어느 구간])</div>
</div>
```

```css
.guardrail-row    { padding: 6px 8px; border-radius: 4px; margin: 4px 0; font-size: 13px; }
.guardrail-danger { background: rgba(248, 81, 73, 0.15); color: var(--red); }
.guardrail-warn   { background: rgba(227, 179, 65, 0.15); color: var(--yellow); }
.guardrail-caution{ background: rgba(139, 148, 158, 0.15); color: var(--text-muted); }
```

위반 0건이면 카드 본문에 한 줄: `<div class="up">✅ 모든 한도 내</div>`.

---

## 상대성과 카드 패턴 (4b)

```html
<div class="card">
  <div class="card-title">📊 상대성과 (오늘)</div>
  <table class="data-table">
    <tr><td>내 포트폴리오</td><td class="up">+[%]</td><td class="muted">기준</td></tr>
    <tr><td>S&P 500</td><td>[변동%]</td><td>[차이 %p]</td></tr>
    <tr><td>NASDAQ 100</td><td>[변동%]</td><td>[차이 %p]</td></tr>
    <tr><td>SOXX</td><td>[변동%]</td><td>[차이 %p]</td></tr>
  </table>
  <div class="muted">핵심 벤치마크: [매일 사용자 최대 테마 기반으로 결정]</div>
</div>
```

---

## 회고 카드 패턴 (12, 조건부)

월요일이면 7일 / 매월 1일이면 30일. 평일에는 카드 자체 미렌더링.

```html
<div class="card">
  <div class="card-title">📊 주간 추천 회고 (YYYY-MM-DD ~ YYYY-MM-DD)</div>
  <div>추천 매수 [N] / 매도 [N] / 보류 [N] · 적중률 [A]/[B] ([%])</div>
  <div>평균 수익률 [%] (벤치마크 대비 [%]p)</div>

  <div class="card-title" style="margin-top:12px;">🟢 잘 된 추천</div>
  <table class="data-table">
    <tr><td>[종목] (점수 [N])</td><td class="up">+[%]</td><td class="muted">[적중 원인 카테고리]</td></tr>
  </table>

  <div class="card-title" style="margin-top:12px;">🔴 실패한 추천</div>
  <table class="data-table">
    <tr>
      <td>[종목] (점수 [N])</td>
      <td class="down">−[%]</td>
      <td class="muted">실패 카테고리: [거시 오판/리스크 누락/이벤트 직전/타이밍]</td>
    </tr>
  </table>

  <div class="muted" style="margin-top:8px;">💡 학습: [회고에서 도출한 패턴 1줄]</div>
</div>
```

---

## 반응형 미디어 쿼리

```css
@media (max-width: 480px) {
  body { padding: 8px; font-size: 13px; }
  .card { padding: 10px; }
  .data-table { font-size: 12px; }
  .data-table th, .data-table td { padding: 6px 4px; }
}
```

---

## 출력 검증

대시보드 작성 후 다음 자체 점검:
- [ ] 11(+1) 표준 섹션 순서대로 배치됐는가 (12는 월요일/매월 1일만)
- [ ] 모드별 배너가 최상단에 있는가
- [ ] 색상 코딩이 의미(상승/하락/주의/중립)에 맞는가
- [ ] 모바일 폭(320px)에서 표가 잘리지 않는가
- [ ] 시세 앵커 트리거 가격이 숫자로 명시됐는가
- [ ] `anchors_source` 가 stale 이면 표기됐는가
- [ ] **4b 상대성과 카드** 가 포트폴리오 안에 있는가 (S&P/NDX/SOXX 비교)
- [ ] **4c 가드레일 카드** 가 3단계 색상으로 표시되는가
- [ ] 신규 매수 후보(8번)에 **100점 점수표** 가 종목별로 들어있는가
- [ ] 보류 후보는 보류 사유가 명시됐는가
- [ ] 오늘이 월요일/매월 1일이면 **12번 회고 카드** 가 렌더링됐는가
