# daily-briefing-skill

Anthropic Claude Code skills that run as scheduled remote routines (Anthropic's
managed cloud).

| Skill | When | Output |
|-------|------|--------|
| `daily-briefing` | Daily 07:00 KST (before KRX open) | Compact telegram summary + full HTML dashboard + clickable button |
| `evening-update` | Daily 22:00 KST (before US open) | Compact (~800 chars) delta telegram + light delta dashboard. Reports only what changed since the morning brief. |
| `retro` | Every Sunday 21:00 KST (auto-promotes to 30-day on the month's first Sunday) | Telegram retro + HTML retro dashboard, opens auto-PR when failure patterns repeat |

All skills pull portfolio data from `portfolio_mcp` and deliver via
`notifier_mcp`. Telegram messages are summaries / triggers; the linked
HTML dashboard always carries the full content (narrative, sizing
rationale, entry/stop/target, hidden risk).

## Skill locations

```
.claude/skills/daily-briefing/SKILL.md
.claude/skills/evening-update/SKILL.md
.claude/skills/retro/SKILL.md
```

Claude Code's routine runner clones this repo and discovers the skills at the
above paths. The frontmatter `name:` lets you invoke them as `/daily-briefing`,
`/evening-update`, or `/retro [weekly|monthly]`.

## Single routine, two fire times (recommended)

Instead of two morning/evening routines, register **one routine** with cron
`0 7,22 * * *` (KST timezone) and a router prompt that branches by hour:

```
오늘 [YYYY-MM-DD] routine.

현재 KST 시각 확인 후 분기:
- 06~09시: /daily-briefing 실행 (morning, 풀 brief)
- 21~23시: /evening-update 실행 (evening, delta update)
- 그 외: 비정상 호출 → 즉시 종료

발송·백업은 각 skill 의 Step 흐름 그대로.

도구: portfolio_mcp / notifier_mcp / WebSearch
```

Retro stays on its own weekly routine (different cadence).

## Required MCP connectors

The remote routine must have these two MCP connectors attached:

| Connector | URL | Purpose |
|-----------|-----|---------|
| `portfolio_mcp` | `https://stock-portfolio-mcp.onrender.com/mcp?token=...` | KIS account, sectors, realized P&L, tax sim |
| `notifier_mcp` | `https://notifier-mcp.onrender.com/mcp?token=...` | Telegram send, dashboard publish, GitHub backup |

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

## Macro indicators (Step 2)

Baseline 8 (daily, for consistency + Step 3 input):
- Core 5: VIX, US 10Y Treasury, DXY, WTI crude, Gold
- Crisis-leading 3: 10Y-2Y spread, HY credit spread, today/this-week
  event calendar (FOMC, CPI, NFP, earnings)

AI may add additional context-specific indicators on top of the baseline
when warranted (e.g., regional FX, sector indices, defense-related
gauges during geopolitical events). Additions are narrated with reason.

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
