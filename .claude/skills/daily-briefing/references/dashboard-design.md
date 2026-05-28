# HTML 대시보드 디자인 가이드

**언제 읽나**: Step 9 (HTML 대시보드 작성) 진입 시. 매일 발행이므로 사실상 매일 1회.
**역할**: 모바일 친화 다크 테마의 일관된 디자인 적용. 색상 코딩과 레이아웃 표준 통일.

> **대시보드 = 진짜 풀 콘텐츠.** 텔레그램은 요약/trigger 일 뿐 — 사용자가 button 누르면 *여기서* 모든 디테일을 본다. 신규 후보 narrative, 사이즈 근거, 진입/손절/익절 가격, hidden risk, 매수 전 확인사항, 종목별 시세 분석 등 *모든 detail 은 대시보드에*. SKILL.md 본문이 "텔레그램엔 종목명·한 줄만" 이라고 한 것의 *반대편 책임* 을 진다.

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
| 기회 | `#1a4a3a` | `#56d364` | 🟢 |
| 액션 | `#1a3a5a` | `#58a6ff` | 🎯 |
| 리마인드 | `#5a4a1a` | `#e3b341` | ⚠️ |
| 안정 | `#1a4a2a` | `#56d364` | ✅ |

```html
<div class="banner banner-crisis">
  🚨 위기 시그널 — [핵심 trigger 한 줄]
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
.banner-opportunity { background: #1a4a3a; color: #56d364; }
.banner-action   { background: #1a3a5a; color: #58a6ff; }
.banner-remind   { background: #5a4a1a; color: #e3b341; }
.banner-stable   { background: #1a4a2a; color: #56d364; }
```

---

## 표준 섹션 (순서 고정)

대시보드 카드는 다음 순서로 배치:

1. **헤더** (날짜, 모드 표시 배너 — 위기 시 핵심 trigger 한 줄)
2. **거시 환경**: baseline 8개 지표 표 + AI 자율 추가 지표 + 위기·기회 시그널 평가 narrative
3. **포트폴리오 현황** (3개 하위 카드):
   - 3a. 미국 + 한국 분리 표 (종목별 평가손익·비중)
   - 3b. **상대성과 카드** — 포트폴리오 vs S&P500 / NDX / SOXX / KOSPI 일일 변동률 + 핵심 벤치마크 대비 ±x.x%p
   - 3c. **비중 모니터링 카드** — 🔴 위험 / 🟠 경고 / 🟡 주의 단계별 표시 (AI 자율 판단, 정해진 % 임계값 없음). 없으면 ✅ 한 줄
4. **추천 추적**: ✅ 실행됨 / ⚠️ 미체결 유효. 각 종목별 *현재가·진입가·재검증 한 줄*
5. **보유 종목 분석**: AI 가 의미 있다고 판단한 변동 종목 + 주기적 리스크 점검 결과 narrative. 없으면 "특이사항 없음"
6. **🎯 오늘의 액션**: 모드별 (위기/액션/기회 등) — 보유 종목 기준 매도/매수, 시세 앵커 기반 진입/익절/손절 가격·근거 풀 narrative
7. **🆕 신규 매수 후보** (최대 5개, 추천 강도 순): 각 후보별 **풀 narrative 추천** — 강점·약점 균형 평가, hidden risk, 시세 앵커 기반 진입가/손절/익절, 권고 사이즈 + 근거. 점수표 없음. 5개 채울 필요 없음.
   - 7b. **🔍 AI 가 보류 권고한 후보 (조건부)** — AI 가 매력적이라 판단했으나 timing·환율·이벤트·현금 같은 *맥락 요인* 으로 보류 권고한 후보가 있을 때만 렌더링. 보류 사유·한 줄 평 노출
8. **📋 매수 전 확인사항**: AI 가 오늘 추천한 종목·매수 상황에 맞춰 narrative 체크 항목 — 환율·세금·이벤트·앵커·집중도 등
9. **세금 시뮬레이션**: KIS + Kiwoom 합산, 공제 잔여, 예상 세금
10. **현금/입금 가이드**: 매수가능 현금. 신규 입금 감지 시 분배 추천 별도 강조
11. **이번 주 일정**: FOMC, 어닝, 경제지표 narrative

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

## 추천 매수 카드 패턴 (풀 narrative, fresh + carry-over 통합)

대시보드의 추천 매수 섹션 (7번) 은 *진짜 풀 디테일* — 텔레그램이 한 줄로 요약한 그 내용. fresh 발굴과 carry-over (Step 6 미체결+유효) 가 *통합 ranking* 되어 등장.

```html
<div class="card candidate-card">
  <div class="card-title">
    [순위]. [종목] ([티커])
    <span class="badge badge-new">NEW</span>
    <!-- 또는 carry-over: -->
    <span class="badge badge-carryover">carry-over · Day [N]</span>
  </div>
  <div class="card-body">
    <div class="narrative"><b>추천 사유:</b> [한 줄 요약]</div>

    <!-- carry-over 인 경우 추가 -->
    <div class="narrative muted">
      <b>처음 추천:</b> [YYYY-MM-DD] / 그동안 미체결 / 오늘도 유효한 이유: [한 줄]
    </div>

    <div class="narrative" style="margin-top:8px;">
      <b>강점:</b> [narrative 한두 줄 — 펀더·밸류·모멘텀·catalyst 중 결정적인 것]
    </div>
    <div class="narrative">
      <b>약점:</b> [narrative 한두 줄 — cherry-pick 금지]
    </div>
    <div class="narrative">
      <b>Hidden risk:</b> [한 줄 — 의무 표기]
    </div>

    <table class="data-table" style="margin-top:8px;">
      <tr><td>진입가</td><td>[값] (근거: [앵커 조합])</td></tr>
      <tr><td>손절</td><td class="down">[값]</td></tr>
      <tr><td>익절</td><td class="up">[값]</td></tr>
    </table>

    <div class="narrative" style="margin-top:8px;">
      <b>권고 사이즈:</b> [액수 / 주수]<br>
      <span class="muted">근거: [모드·컨빅션·변동성·세금·노출 narrative 한두 줄]</span>
    </div>
  </div>
</div>
```

```css
.candidate-card { border-left: 3px solid var(--accent); }
.narrative { font-size: 13px; line-height: 1.6; margin: 4px 0; }
.muted { color: var(--text-muted); font-size: 12px; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 12px; margin-left: 6px; }
.badge-new        { background: rgba(86, 211, 100, 0.15); color: var(--green); }
.badge-carryover  { background: rgba(88, 166, 255, 0.15); color: var(--accent); }
```

**점수표·매력 N/M 배지 금지** — narrative 로만 매력도 표현. 순위는 추천 강도 순 정렬로 표시 (1위가 가장 강한 추천).

**NEW vs carry-over** 라벨은 *origin 표시일 뿐* ranking 영향 X — 매일 fresh 와 carry-over 가 동등하게 경쟁해서 ranking. carry-over 가 5위권 밖으로 밀려나면 silent expire.

---

## 헤지 제안 카드 패턴 (별도, 위기/이벤트 모드 한정)

**일반 매수 후보 카드와 *완전히 분리*** — 헤지는 *수익 추구 X, 단기 보험*. 평상시 렌더링 X, 위기 모드 또는 강한 이벤트 리스크 시에만.

```html
<div class="card hedge-card">
  <div class="card-title">🛡️ 단기 헤지 제안</div>
  <div class="narrative"><b>목적:</b> [예: FOMC 직전 단기 하방 완충 / AI 섹터 과열 대응 등]</div>
  <div class="narrative"><b>수단:</b> [카테고리 — 지수 인버스 ETF / 섹터 인버스 / 변동성 상품 / 단기채 등]</div>
  <div class="narrative"><b>권고 사이즈:</b> [포트폴리오의 일부 — 완전 상쇄 X. 예: 미국 노출의 5~10%]</div>
  <div class="narrative"><b>예상 보유 기간:</b> [며칠~몇 주. *장기 보유 금지*]</div>
  <div class="narrative"><b>해제 조건:</b> [예: VIX 안정, 이벤트 통과, 지수 지지 회복]</div>
  <div class="narrative"><b>손절/무효화:</b> [헤지 자체 손실 한계 — 예: -X% 시 청산]</div>
  <div class="narrative"><b>왜 매도보다 헤지가 나은가:</b> [세금·재진입·thesis 유지 측면 narrative]</div>
  <div class="narrative muted">⚠️ 인버스/레버리지 상품은 decay·추적오차 — 장기 보유 대상 X.</div>
</div>
```

```css
.hedge-card { border-left: 3px solid var(--yellow); }
```

(border 색상이 일반 candidate-card 의 accent 와 달라 사용자가 *다른 카테고리* 임을 즉시 인식)

**렌더링 조건:**
- 위기 모드 (Step 3 위기 강함 판정) — crisis-playbook.md 의 3가지 옵션 중 헤지 검토
- 평상 모드 + 강한 이벤트 리스크 (FOMC·CPI·주요 어닝 직전) — 선택적
- 평상 모드 + 이벤트 없음 → **카드 자체 미렌더링**

### 추천 0개일 때 카드 (과매매 방지 강조)

오늘 fresh + carry-over 통합 결과 추천할 만한 종목이 *0개* 일 때 — 섹션 자체를 생략하지 말고 *명시적으로 0개임을 표시*. 사용자가 "AI 가 분석 안 했나?" 오해 방지 + 현금 보유가 정당한 선택임을 강조:

```html
<div class="card candidate-card candidate-empty">
  <div class="card-title">🆕 추천 매수 후보</div>
  <div class="narrative">
    <b>오늘은 신규/추가 매수 권장 없음.</b><br>
    fresh 발굴 + carry-over 통합 결과 *오늘 기준 진입 매력이 충분한 후보 없음*.
    현금 보유가 최선으로 판단.
  </div>
  <div class="narrative muted" style="margin-top:6px;">
    💡 추천 0개는 정상. 매일 액션이 있어야 한다는 압박은 과매매 위험.
    내일 brief 에서 새 catalyst 보고 재검토.
  </div>
</div>
```

```css
.candidate-empty { border-left-color: var(--text-muted); }
```

매력적인 후보가 1개라도 있으면 일반 카드 사용. 0개 케이스 전용 패턴.

---

## 시세 앵커 트리거 가격 표시 패턴

종목별 익절·손절 가격을 보여줄 때. AI 가 시세 앵커(ma50·ma200·atr20·52w) 를 *어떻게* 조합해서 가격을 산출했는지 사용자가 검증할 수 있게 근거 컬럼 포함.

```html
<div class="trigger-card">
  <div class="trigger-symbol">[종목] <span class="muted">비중 [X]%</span></div>
  <table class="trigger-table">
    <tr><td>익절 트리거</td><td class="up">$[값]</td><td class="muted">[AI 가 사용한 앵커 조합 — 종목 특성·시장 상황 보고 판단]</td></tr>
    <tr><td>손절 트리거</td><td class="down">$[값]</td><td class="muted">[근거]</td></tr>
    <tr><td>현재가</td><td>$[값]</td><td class="muted">(stale: YYYY-MM-DD 캐시 — stale 시만)</td></tr>
  </table>
</div>
```

`anchors_source == "yfinance:stale"` 인 경우 마지막 행에 `(stale: YYYY-MM-DD 캐시)` 명시.

---

## 비중 모니터링 카드 패턴 (3c)

3단계를 색상으로 구분. 같은 색 코드를 banner 와 일치. **% 임계값 없음** — AI 가 portfolio 컨텍스트·종목 성격 보고 자율 판단.

```html
<div class="card">
  <div class="card-title">📊 포트폴리오 비중 모니터링</div>
  <div class="weight-row weight-danger">🔴 위험: [항목] [값] — [한 줄 사유]</div>
  <div class="weight-row weight-warn">🟠 경고: [항목] [값] — [한 줄 사유]</div>
  <div class="weight-row weight-caution">🟡 주의: [항목] [값] — [한 줄 사유]</div>
</div>
```

```css
.weight-row     { padding: 6px 8px; border-radius: 4px; margin: 4px 0; font-size: 13px; }
.weight-danger  { background: rgba(248, 81, 73, 0.15); color: var(--red); }
.weight-warn    { background: rgba(227, 179, 65, 0.15); color: var(--yellow); }
.weight-caution { background: rgba(139, 148, 158, 0.15); color: var(--text-muted); }
```

해당 단계 없으면 줄 생략. 전혀 없으면 카드 본문에 한 줄: `<div class="up">✅ 모든 항목 안정</div>`.

---

## 상대성과 카드 패턴 (3b)

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

## AI 가 보류 권고한 후보 카드 패턴 (7b, 조건부)

AI 가 매력적이라 판단했으나 timing·환율·이벤트·현금 같은 *맥락* 요인으로 보류 권고한 후보가 있을 때만 렌더링.
없으면 카드 자체 생략.

```html
<div class="card">
  <div class="card-title">🔍 참고: AI 가 보류 권고한 후보</div>
  <table class="data-table">
    <tr>
      <td>[종목]</td>
      <td class="muted">보류 사유: [맥락 요인]</td>
    </tr>
    <tr>
      <td colspan="2" class="muted">→ [한 줄 평 — 어떤 매력이 있는데 무엇 때문에 미루는지]</td>
    </tr>
  </table>
  <div class="muted" style="margin-top:8px;">사용자가 직접 판단하여 사후 진입 검토 가능.</div>
</div>
```

> **회고는 별도 `retro` skill 의 대시보드에** — daily-briefing 대시보드엔 회고 카드 없음.

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
- [ ] 11개 표준 섹션 순서대로 배치됐는가
- [ ] 모드별 배너가 최상단에 있는가 (위기 시 핵심 trigger 한 줄 포함)
- [ ] 색상 코딩이 의미(상승/하락/주의/중립)에 맞는가
- [ ] 모바일 폭(320px)에서 표가 잘리지 않는가
- [ ] 시세 앵커 트리거 가격이 숫자로 명시됐는가
- [ ] `anchors_source` 가 stale 이면 표기됐는가
- [ ] **3b 상대성과 카드** 가 포트폴리오 안에 있는가 (S&P/NDX/SOXX 비교)
- [ ] **3c 비중 모니터링 카드** 가 3단계 색상으로 표시되는가 (AI 자율 판단, % 임계값 없음)
- [ ] **신규 매수 후보 카드(7번)** 가 종목별 풀 narrative 인가 (추천 사유·강점·약점·hidden risk·진입/손절/익절·권고 사이즈+근거). 점수표·매력 N/M 배지 없음. 최대 5개, 추천 강도 순.
- [ ] AI 가 보류 권고한 후보(7b) 있으면 사유와 한 줄 평 명시됐는가
- [ ] 매수 전 확인사항(8번) narrative 가 오늘 추천에 맞춰 작성됐는가
- [ ] 텔레그램이 한 줄만 요약한 detail 들이 *모두 대시보드에* 들어있는가 (사용자가 텔레그램 button 누르면 충분한 정보 얻을 수 있게)
