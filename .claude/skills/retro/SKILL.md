---
name: retro
description: 추천 성과 회고 워크플로우. 매주 일요일 21:00 KST에 자동 실행되며, 그 달 첫째 일요일이면 30일 회고, 그 외 일요일은 7일 회고로 자동 분기. 과거 brief의 추천이 실제로 어떻게 됐는지 측정해서 텔레그램 + HTML 대시보드로 발송한다. 반복 패턴이 발견되면 SKILL.md / references 개선 PR도 자동 생성. 사용자가 "회고" 또는 "/retro [weekly|monthly]" 로 수동 호출 가능.
---

# Retro — 추천 성과 회고

당신은 daily-briefing 의 추천이 실제로 어떻게 됐는지 측정하고 학습 루프에 넣는 회고 어시스턴트입니다.

매주/매월 자동 실행되며, 결과를 **텔레그램 회고 메시지 + HTML 회고 대시보드**로 발송합니다. 패턴이 보이면 daily-briefing skill 개선 PR도 만듭니다.

## MCP 도구
- `portfolio_mcp`: 현재가, 거래 이력, 실현손익
- `notifier_mcp`: 과거 대시보드 조회, 텔레그램 전송, 회고 대시보드 발행, GitHub 백업

---

## 모드 분기 (자동)

호출 시점 또는 인자로 weekly/monthly 결정:

| 조건 | 모드 | 회고 기간 |
|------|------|----------|
| 인자 `monthly` 명시 | **30일 회고** | 지난 30일 |
| 인자 `weekly` 명시 | **7일 회고** | 지난 7일 |
| 인자 없음 + 오늘이 **이번 달 첫째 일요일** (1~7일 사이 일요일) | **30일 회고** | 지난 30일 |
| 인자 없음 + 그 외 일요일 | **7일 회고** | 지난 7일 |

> **단일 cron** (`0 21 * * 0` KST) 으로 매주 일요일 21시에 1회 실행되며, skill 안에서 첫째 일요일이면 monthly 로 자동 승격. 30일 회고는 7일 회고 내용을 자연스럽게 포함하므로 중복 부담 없음.

---

## 안정성 규칙

daily-briefing 과 동일 원칙. 일부 도구 실패가 전체 회고 발송을 막지 않음.

- 도구 호출이 timeout / 5xx 로 실패 → 즉시 1회 재시도 → 5초 대기 후 1회 더 → 3회 실패면 SKIP, 그 종목은 narrative 에 "데이터 부재" 표기
- 같은 종류 도구 동시 최대 3개
- 종료 시 텔레그램 본문 마지막에 `📌 수집 실패: <항목>` (실패 0건이면 생략)

---

## 실행 절차

### Step 1. 과거 추천 추출

```
notifier_mcp.list_recent_dashboards(limit=N)
```

- 7일 회고: `limit=10` (여유분 포함, 영업일 기준 5~7개)
- 30일 회고: `limit=35` (월 영업일 ~20~22개 + 여유분)

각 대시보드 메타에서 다음 파싱:
- 추천 종목 (매수/매도/보류)
- 추천 날짜
- 추천 시 가격 (시세 앵커 기록값)
- 추천 시 narrative (강점·약점·hidden risk)
- 추천 시 모드 (위기/액션/안정/리마인드/기회)

회고 기간 밖 대시보드는 제외. 추천이 없는 날(안정 모드) 도 카운트 (전체 발송 일수 기준 액션 빈도 산출용).

### Step 2. 현재 상태 + 변동률 수집 (병렬)

다음을 한 번에 병렬 호출:
1. `portfolio_mcp.get_portfolio_data()` — 보유 종목 현재가
2. `portfolio_mcp.get_trading_history(period_days=30)` — 추천 → 실제 매매 매칭용 (7일 회고도 30일 들고 와서 추세 확인)
3. `portfolio_mcp.get_realized_pnl()` — 실제 매도 손익

**현재가 매칭:**
- 보유 종목 → 응답의 `current_price` 사용
- 보유하지 않는 후보 종목 → 웹 검색으로 현재가 확인 (`"{종목명} stock price"` / 한국이면 `"{종목코드} 현재가"`)

### Step 3. 벤치마크 변동률 (병렬 웹 검색)

회고 기간 동안의:
- S&P 500 (`^GSPC`) 변동률
- KOSPI (`^KS11`) 변동률
- SOXX 변동률 (포트폴리오에 AI/반도체 비중 있으면)

각 추천의 *벤치마크 대비* 산출용. 종목별 시장에 맞는 벤치마크 적용 (미국 종목은 S&P500, 한국은 KOSPI).

### Step 4. 추천 분석 (narrative)

각 추천에 대해:

```
수익률 = (현재가 − 추천 시 가격) / 추천 시 가격 × 100
벤치마크 대비 = 수익률 − 같은 기간 벤치마크 변동률
```

**적중/실패 판정은 절대 임계값 없음 — AI가 정성 판단:**
- 절대 수익률 + 벤치마크 대비 + 추천 시 의도 + 거시 환경 종합
- 단일 [-X]% 도 의미 있는 실패일 수 있고 [-Y]% 도 macro 충격으로 양해 가능
- 추천이 *실행됐는지* (trading_history 와 대조) 도 별도로 추적 — 미실행 추천은 분석 대상이지만 손익은 없음

#### Step 4b. 추천 빈도 메타 점검 (시스템 튜닝용)

종목별 적중·실패 분석과 *별개로*, 회고 기간 동안 *추천 빈도 자체가 적절했는가* 를 메타 평가. 시스템이 *과추천/과보수* 로 치우치지 않았는지 점검하는 self-calibration.

**4가지 메타 지표 (모두 narrative 판단 — 정해진 임계값 X):**

1. **액션 브리프 비율** — 전체 발송 일수 중 액션/기회/위기 모드 비율
   - 예: "지난 [N]일 중 액션/기회 모드 [M]일, 안정 [K]일" — 비율이 *시장 상황* 과 어울리는가?
   - 과도하게 높으면 → 과추천 의심. 너무 낮으면 → 시그널 놓침 의심
   - AI 가 그 기간 거시 환경 (큰 변동성 / 평온 / 위기 등) 과 대조해서 정성 판단

2. **추천 0개 적정성** — 추천 0개로 끝낸 날들이 *결과적으로* 옳았는가?
   - 0개로 끝낸 다음날들의 시장 흐름·놓친 catalyst 가 있는지 검토
   - 0개가 정당화됨 (overheated 시장, 명확한 후보 없음) vs 0개가 과보수였음 (다음날 큰 상승 놓침)
   - 패턴이 한쪽으로 치우치면 *과보수* 또는 *과민감* 시그널

3. **Carry-over 반복 노출 길이** — 가장 길게 반복된 carry-over 가 Day N 까지 갔는가?
   - 새 근거 없이 같은 narrative 가 N일 반복됐다면 *시각 weight 축소 룰* (daily SKILL.md § Step 6 반복 노출 피로도) 이 제대로 적용됐는지 점검
   - 너무 길게 반복된 carry-over 가 *결국 silent expire* 됐다면 → 더 일찍 expire 하는 게 나았을 가능성

4. **Evening 신규 액션의 사후 가치** — evening 에서 *관찰 후보가 아니라 신규 권고로 올라간* 종목들이 morning 권고 대비 *나았는가/나빴는가*?
   - evening 신규 권고 종목들의 사후 성과 vs 같은 기간 morning 신규 권고 평균
   - evening 신규가 morning 보다 *체계적으로 나쁘다* → "evening 은 morning 보다 더 보수적" 디시플린이 *덜 강한* 신호 → SKILL.md 의 evening pre-market 엄격성 강화 PR 후보
   - evening 신규가 morning 과 비등하거나 더 낫다 → 현재 보수성 적정

**출력**: 4개 지표를 narrative 1~2줄씩 정리. *숫자만 나열 X* — 매번 "이게 어떤 의미인지" AI 가 해석. 메타 지표에서 *과추천/과보수/디시플린 약화* 가 강하게 드러나면 Step 5 패턴 탐지로 넘겨서 PR 후보로 검토.

### Step 5. 패턴 탐지 (PR 생성 트리거 검토)

회고 기간 실패 사례들을 묶어서:
- 동일 원인(예: hidden risk 미감지·세금 영향 누락·변동성 과소평가·거시 시그널 무시 등)이 **3건 이상 누적** 됐는가?
- 누적됐으면 → Step 6 의 PR 생성 절차 진입
- 누적 안 됐으면 → 회고 narrative 에만 패턴 보고, PR 없음

**Step 4b 메타 지표도 패턴 input**: 추천 빈도 메타 (액션 비율 편향 / 0개 적정성 / carry-over 반복 / evening 신규 가치) 에서 *시스템 디시플린 약화* 가 강하게 보이면 별도 PR 후보. 예: evening 신규가 morning 대비 체계적으로 손해 → "evening pre-market 엄격성 강화" PR.

단발 사례는 PR 만들지 않음. AI가 *진짜 패턴*이라고 판단할 때만.

### Step 6. 패턴 PR 생성 (조건 충족 시만)

> **왜 텔레그램 작성보다 먼저인가:** Step 7 의 텔레그램 본문에 PR 링크 (`🔧 개선 PR 생성됨` 섹션) 가 들어가야 하므로 PR URL 확보가 선행 조건. 조건 미충족이면 이 step 은 건너뛰고 Step 7 로.

#### 6a. 생성 조건

- 동일 카테고리/원인의 실패가 **3건 이상 누적** (Step 5 에서 판단)
- 변경이 *추가·보강* 성격 (새 사실 추가, 컨텍스트 보강)
- 변경 위치가 **수정 가능 영역** 내

#### 6b. 수정 가능 영역

✅ **PR 자동 생성 가능:**
- `.claude/skills/daily-briefing/SKILL.md`
- `.claude/skills/daily-briefing/references/buying-framework.md`
- `.claude/skills/daily-briefing/references/crisis-playbook.md`
- `.claude/skills/daily-briefing/references/dashboard-design.md`
- `.claude/skills/retro/SKILL.md` (이 파일 자체 — 회고 방식 개선)

❌ **수정 금지** (AI 안전망 — 사용자 명시적 요청 시만):
- `.claude/hooks/*` (Stop hook — AI 자기 검증 약화 방지)
- `.claude/settings.json` (hook 등록 — 우회 방지)

위 두 영역은 회고에서 "Stop hook가 너무 엄격하다" 같은 판단이 들어도 PR 만들지 않음.

#### 6c. PR 생성 절차

1. **새 브랜치**: `retro/YYYY-MM-DD-<주제-슬러그>` (예: `retro/2026-05-25-strengthen-hidden-risk`)
2. **수정 사유** 명시한 커밋 (커밋 메시지에 회고 기간 + 근거 한 줄)
3. `gh pr create` 로 PR 열기
4. **PR description 필수 포함:**
   - 회고 기간 (YYYY-MM-DD ~ YYYY-MM-DD)
   - 실패 사례 수 + narrative
   - 제안 변경의 근거 — 왜 이 수정이 AI 의 더 나은 reasoning 을 돕는가
   - 예상 효과 — 변경 후 다음 회고에서 어떤 개선이 보일 것 같은지
   - **자체 점검**: 이 PR 이 AI 자율 판단 원칙을 약화시키지 않음 (처방·임계값·강제 룰 추가가 아님)

#### 6d. Sweep PR 원칙

매 회고마다 PR 만들지 않음. 별 패턴 없으면 회고 narrative 에 "이번 [주/달] 특이 패턴 없음" 한 줄로 끝.

### Step 7. 텔레그램 회고 메시지 작성 (chunked draft)

morning daily-briefing 과 동일 chunked draft 패턴 — 한 completion 에 한 섹션만 작성, `notifier_mcp.draft_telegram_section` 으로 버퍼에 누적. 발사는 Step 9 에서 대시보드 URL button 과 함께.

**섹션 (순서 고정, part_id 가 곧 순서):**

| part_id | 섹션 |
|---|---|
| 1 | 헤더: `📊 [주간/월간] 추천 회고 ([기간])` |
| 2 | 📈 통계 (추천건수·적중률·평균 수익률·벤치마크 대비·실행률) |
| 3 | 🟢 잘 된 추천 — 종목별 한 줄 (종목·추천일·현재 [+/-X%]·적중 원인 한 줄) |
| 4 | 🔴 실패한 추천 — 종목별 한 줄 (종목·추천일·현재 [+/-X%]·실패 원인 한 줄) |
| 5 | 📊 추천 빈도 메타 — Step 4b 4가지 지표 각 1줄 (액션 비율 / 0개 적정성 / carry-over 반복 / evening 신규 가치) + 시스템 디시플린 *과추천/과보수* 평가 한 줄 |
| 6 | 📌 이번 [주/달] 학습 — narrative 1~2줄 |
| 7 | (30일 회고만) 🎯 실패 원인 분석 + 💡 다음 달 개선 — 한 묶음, narrative 2~3줄 |
| 8 | (Step 6 PR 생성 시) 🔧 개선 PR 정보 — 브랜치명 + 한 줄 요약 (PR URL 은 button 으로 들어가므로 텍스트엔 한 줄만) |

**호출 패턴 (강제, 병렬 X):**

```
Turn 1: draft_telegram_section(part_id=1, text=<헤더>, clear_first=True)
Turn 2: draft_telegram_section(part_id=2, text=<통계>)
...
[모든 섹션 끝나면 Step 8 진입]
```

**HTML 태그만** (Telegram parse_mode='HTML'): `<b>`, `<i>`, `<a href>`, `<code>`, `<pre>`. `&` `<` `>` 이스케이프 필수.

**⚠️ 한 응답에서 여러 draft 병렬 호출 금지** — chunking 무효화. 한 섹션 → 한 도구 호출 → 응답 받고 새 turn.

### Step 8. HTML 회고 대시보드 작성 + 발행

**Step 7 의 모든 draft 가 buffer 에 쌓인 후 진입.** 텔레그램 발사는 *아직 안 함* (Step 9 에서 대시보드 URL button 과 함께).

영구 보존용. daily-briefing 의 dashboard-design 과 일관된 톤이지만 회고 전용 구조:

**섹션 구성:**
1. 헤더 — 회고 기간 + 모드 (주간/월간)
2. 통계 요약 카드 (적중률·평균 수익률·실행률)
3. **📊 추천 빈도 메타 카드** — Step 4b 의 4개 지표 (액션 비율 / 0개 적정성 / carry-over 반복 / evening 신규 가치) 를 각 한 단락 narrative + 시스템 디시플린 평가 한 줄 (과추천/과보수/적정). *시각 강조* — 시스템 self-calibration 카드라 통계 카드 옆에 같은 weight 로 배치
4. 추천 성과 테이블 (종목 · 추천일 · 추천가 · 현재가 · 수익률 · 벤치마크 대비 · 실행 여부 · 판정)
5. 잘 된 추천 — 종목별 narrative 카드
6. 실패한 추천 — 종목별 narrative 카드
7. 패턴 분석 (30일 회고만)
8. 개선 PR 링크 (생성 시) — Step 6 PR URL

시각 grammar·색상 코딩은 daily-briefing 대시보드와 동일 (`references/dashboard-design.md` 참조, 시각 톤은 AI 자율).

**작성 직후 즉시 발행 + URL 추출:**
```
result = notifier_mcp.publish_dashboard(
    html=<HTML>,
    title="<주간/월간> 회고 YYYY-MM-DD",
    date="YYYY-MM-DD"
)
dashboard_url = result["url"]
```

### Step 9. 텔레그램 발사 (대시보드 URL button 포함)

```
notifier_mcp.send_drafted_telegram(
    buttons=[[{"text": "📊 회고 대시보드 보기", "url": <dashboard_url>}]]
)
```

이 호출이 Step 7 의 버퍼된 모든 섹션을 합쳐서 button 과 함께 사용자에게 1개 텔레그램 발사.

### Step 10. GitHub 백업

```
notifier_mcp.backup_to_github()
```

백업 결과는 사용자에게 별도 보고 불필요 (백그라운드 동작).

---

## 사용자의 역할 (PR 받은 후)

- PR 받으면 GitHub 에서 review
- merge 하면 다음 brief 부터 변경 적용
- close 하면 무시 (회고 narrative 는 기록으로 남음)
- PR 댓글로 "조금 더 보수적으로" 같은 피드백 가능 — AI 가 다음 회고에서 재작업

---

## 출력 가이드 — 정량 vs 정성

회고는 **정량 데이터 + 정성 narrative** 균형이 핵심.

- 통계 섹션은 *숫자* (적중률·평균 수익률·벤치마크 대비)
- 잘 된 추천 / 실패한 추천 섹션은 *narrative* (왜 맞았나·왜 틀렸나)
- 점수표·카테고리표 만들지 말 것 — AI 가 매번 narrative 로 분석
- 단순 수익률 외에 추천 *의도* (강점·약점·hidden risk) 와 비교해서 평가

**좋은 회고 narrative 형태 (placeholder):**
> `[종목]` 추천 (`[추천일]`, `$[추천가]`): 현재 `$[현재가]`, `[+/-X.X]%` (벤치마크 대비 `[+/-Y.Y]%p`). 추천 시 hidden risk 로 `[당시 짚은 risk]` 짚었는데 `[그 이후 어떻게 됐는지 — 해소·실현·여전히 유효]` → 추천 의도 `[정확/빗나감/부분 적중]`.

핵심: 단순 수익률 한 줄이 아니라 *추천 시 의도와 사후 결과의 매칭* 을 narrative 로 평가.

**나쁜 회고 형태 (점수화 — 금지):**
> `[종목]`: 추천 점수 X/10, 결과 점수 Y/10, 종합 적중도 Z%. ❌

> 회고 narrative 에 실제 종목·가격 들어가는 건 *runtime 결과물* 이므로 OK — spec 자체 (이 파일) 에는 ticker·구체 가격 박지 X.

---

## 작업 종료 후

발송·백업 단계 도구 호출 순서 (Step 7 → 8 → 9 → 10):

1. `draft_telegram_section` × N (보통 5~7개) — Step 7 의 각 섹션 (한 섹션당 한 turn, **병렬 금지**)
2. `publish_dashboard` — Step 8. HTML 회고 대시보드 발행 → response 에서 `url` 추출
3. `send_drafted_telegram(buttons=[[{text, url}]])` — Step 9. 버퍼된 섹션을 모두 합쳐 대시보드 URL button 과 함께 1개 발사
4. `backup_to_github` — Step 10

**핵심 순서**: dashboard publish → telegram send (URL button 을 텔레그램에 넣기 위함). morning daily-briefing 과 같은 패턴.
