# daily-briefing-skill

Anthropic Claude Code skills that run as scheduled remote routines (Anthropic's
managed cloud).

| Skill | When | Output |
|-------|------|--------|
| `watchdog` | Daily 08:40 / 22:40 KST | Checks that each briefing was actually published (and not twice) and both servers answer; alerts the personal Telegram only when something is wrong, plus a Monday heartbeat |
| `market-radar` | Daily 07:30 KST | **Public** market briefing for a Telegram group (no account data): macro, sentiment, sectors, screener watch-list, calendar. Leaves a `market-judgment` JSON block on its dashboard |
| `daily-briefing` | Daily 08:00 KST (before KRX open) | Personal brief = today's public market judgment + this account's holdings, cash, tax and position decisions. Compact telegram summary + full HTML dashboard |
| `evening-update` | Daily 22:00 KST (before US open) | Compact (~800 chars) delta telegram + light delta dashboard. Reports only what changed since the morning brief. |
| `retro` | Every Monday 06:00 KST (auto-promotes to 30-day on the month's first Monday) | Scores recorded recommendations at T+30 / T+90 (return vs benchmark), always picks the worst one and names the missed risk; opens a one-line `[Dynamic Rules]` PR only when that miss was a judgment or process flaw (otherwise records "no rule" with numeric reasons; 3 such retros in a row with negative excess return force a rule candidate for human review) |

All skills pull portfolio data from `portfolio_mcp` and deliver via
`notifier_mcp`. Telegram messages are summaries / triggers; the linked
HTML dashboard always carries the full content (narrative, sizing
rationale, entry/stop/target, hidden risk).

## Skill locations

```
.claude/skills/daily-briefing/SKILL.md
.claude/skills/evening-update/SKILL.md
.claude/skills/retro/SKILL.md
.claude/skills/market-radar/SKILL.md
.claude/skills/watchdog/SKILL.md
```

Claude Code's routine runner clones this repo and discovers the skills at the
above paths. The frontmatter `name:` lets you invoke them as `/daily-briefing`,
`/evening-update`, or `/retro [weekly|monthly]`.

## Routines

Each skill runs as its own Claude Code routine. **Routine cron is evaluated in UTC**,
so the expressions below are UTC values for the KST times shown.

| Routine | Cron (UTC) | KST |
|---------|-----------|-----|
| market-radar (`/market-radar`) — **public connector + notifier only** | `30 22 * * *` | daily 07:30 |
| Daily Portfolio Briefing (`/daily-briefing`) | `0 23 * * *` | daily 08:00 |
| EveningPortfolioUpdate (`/evening-update`) | `0 13 * * *` | daily 22:00 |
| retro-portfolio (`retro`) | `0 21 * * 0` | Monday 06:00 |
| watchdog (`/watchdog`) — `notifier_mcp` only | `40 13,23 * * *` | daily 08:40 / 22:40 |

Routine prompts state the date rule explicitly — the runner announces the fire
time in UTC, so "today" must be computed as UTC + 9h:

```
날짜·요일은 KST(UTC+9) 기준. 실행 안내의 UTC 시각에 9시간을 더해 오늘 날짜를 정할 것.
```

## Required MCP connectors

The three personal routines (daily-briefing, evening-update, retro) get `portfolio_mcp` + `notifier_mcp`. The public `market-radar` routine gets `market_public_mcp` + `notifier_mcp` only. Authentication is header-only.

| Connector | URL | Headers | Purpose |
|-----------|-----|---------|---------|
| `portfolio_mcp` | `https://portfolio-mcp-jdao.onrender.com/mcp` | `Authorization: Bearer <MCP_AUTH_TOKEN>` (server auth) + `X-APP-KEY`, `X-SECRET-KEY`, `X-ACCOUNT-ID` (your KIS key — BYOK) | Account tools (holdings, trades, realized P&L) + public market data (macro, sentiment, sectors, screener, stock analysis, earnings calendar, recommendation scoring) |
| `notifier_mcp` | `https://notifier-mcp.onrender.com/mcp` | `Authorization: Bearer <MCP_AUTH_TOKEN>` | Telegram send, dashboard publish, recommendation records, GitHub backup |
| `market_public_mcp` | `https://portfolio-mcp-jdao.onrender.com/mcp?mode=public` | `Authorization: Bearer <MCP_AUTH_TOKEN>` **only — no KIS key headers** | Same server in `public` mode for the group-chat market briefing: account tools and holdings-based lookups are blocked server-side. The `?mode=public` suffix only makes the URL distinct so it can be registered twice |

- KIS key headers: official names `X-KIS-APP-KEY`, `X-KIS-APP-SECRET`, `X-KIS-ACCOUNT-NO`; the server also accepts the aliases `X-APP-KEY`, `X-SECRET-KEY`, `X-ACCOUNT-ID`.
- The old `?token=...` query URL is **rejected by `portfolio_mcp` since 2026-10-10** (401). Use the header.
- `portfolio_mcp` keeps no KIS key of its own: without the `X-*` key headers it runs in
  `public` mode and the account tools are disabled. Personal skills check
  `get_access_mode` first and stop if `account_data_available` is not true.
- The `market-radar` routine must have **only** `market_public_mcp` + `notifier_mcp` attached. It sends with `channel="public"` (separate bot + group chat fixed on the server via `TELEGRAM_BOT_TOKEN_PUBLIC` / `TELEGRAM_CHAT_ID_PUBLIC`), and its dashboards are isolated from personal ones (prev/next and archive links stay within the public channel).
- When the server adds new tools, enable them in the claude.ai connector settings —
  tools added after the connector was first connected may stay off.

## Modes (telegram tone scales with importance)

Telegram is always compact (~1500 chars for morning, ~800 for evening).
The dashboard always carries full content. The mode shifts only the
telegram header tone and the dashboard button text.

| Mode | Trigger | Telegram header | Dashboard button |
|------|---------|-----------------|------------------|
| 🚨 Crisis | AI judges crisis signals strong (양방향 종합 판단) | LOUD, urgent + trigger one-liner | 🚨 위기 대응 즉시 보기 |
| 🟢 Opportunity | AI judges opportunity signals strong | Clear emphasis | 🟢 기회 분석 보기 |
| 🎯 Action | New buy/sell recommendation surfaced | Medium emphasis | 🎯 액션 상세 보기 |
| ⚠️ Reminder | Prior rec not yet executed (morning only) | Mild emphasis | 📊 미반영 추천 보기 |
| ✅ Stable | All quiet | Subtle | 📊 대시보드 |

## Market analysis (Step 2)

Macro indicators come from one `get_macro_snapshot` call (volatility & sentiment,
rates, credit & liquidity, FX, commodities, equity indices; economy when relevant) instead of
web searches; only the day's event calendar (FOMC, CPI, NFP …) is searched.
Investor sentiment/flows come from `get_investor_sentiment`.

How to read them — indicator labelling, "no data" handling, the two-sided
crisis/opportunity lens, sentiment as supporting evidence only, screener rules —
lives in one shared file so every briefing applies the same principles:

```
.claude/skills/daily-briefing/references/market-analysis.md
```

## Local testing

Clone to your `~/.claude/skills/` (or symlink) for manual `/daily-briefing`
invocation outside the scheduled routine:

```bash
# Windows (PowerShell)
cd $HOME\.claude\skills
git clone https://github.com/kcho32/daily-briefing-skill.git tmp
mv tmp\.claude\skills\daily-briefing .
rm -r tmp
```

## Updating

Edit `.claude/skills/daily-briefing/SKILL.md` and push. The next scheduled run
will use the new version (the routine clones fresh each time).
