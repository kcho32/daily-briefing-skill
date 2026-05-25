# daily-briefing-skill

Anthropic Claude Code skills that run as scheduled remote routines (Anthropic's
managed cloud).

| Skill | When | Output |
|-------|------|--------|
| `daily-briefing` | Daily 07:00 KST | Telegram summary + HTML dashboard |
| `retro` | Every Sunday 21:00 KST (skill auto-promotes to 30-day on the month's first Sunday) | Telegram retro + HTML retro dashboard, opens auto-PR when failure patterns repeat |

Both pull portfolio data from `portfolio_mcp` and deliver via `notifier_mcp`.
`retro` reads past dashboards via `notifier_mcp.list_recent_dashboards` to
measure recommendation outcomes.

## Skill locations

```
.claude/skills/daily-briefing/SKILL.md
.claude/skills/retro/SKILL.md
```

Claude Code's routine runner clones this repo and discovers the skills at the
above paths. The frontmatter `name:` lets you invoke them as `/daily-briefing`
or `/retro [weekly|monthly]`.

## Required MCP connectors

The remote routine must have these two MCP connectors attached:

| Connector | URL | Purpose |
|-----------|-----|---------|
| `portfolio_mcp` | `https://stock-portfolio-mcp.onrender.com/mcp?token=...` | KIS account, sectors, realized P&L, tax sim |
| `notifier_mcp` | `https://notifier-mcp.onrender.com/mcp?token=...` | Telegram send, dashboard publish, GitHub backup |

## Modes (adaptive length)

| Mode | Trigger | Length | Dashboard? |
|------|---------|--------|-----------|
| 🚨 Crisis | VIX>30 / yield curve / spread / portfolio ±5% | Full + emphasis | Yes |
| 🎯 Action | New buy/sell recommendation | Full | Yes |
| ⚠️ Reminder | Prior rec not yet executed | Short | No |
| ✅ Stable | All quiet | Minimal (~300 chars) | No |

## Macro indicators (8 daily web searches)

Core 5:
- VIX (+ daily delta %)
- US 10Y Treasury yield
- DXY
- WTI crude
- Gold

Crisis-leading 3:
- 10Y-2Y spread
- HY credit spread
- Today/this-week event calendar (FOMC, CPI, NFP, earnings)

## Historical comparison

Each run tags the current macro state against one of:
2007-01 / 2007-08 / 2019-11 / 2020-02 / 2022-01 / 2023-01 / normal.

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
