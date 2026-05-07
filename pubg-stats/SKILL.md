---
name: pubg-stats
description: Query and summarize PUBG Steam player match stats whenever the user asks about PUBG 战绩、最近几天表现、吃鸡数据、评级、KDA、近况复盘，提到玩家名和时间范围，或想运行本地 PUBG stats 工具。 Use this skill proactively for requests like “查下某玩家最近 7 天战绩”, “看看我昨天打得怎么样”, “帮我跑一下 pubg stats”, “帮我复盘最近几天 PUBG”, or “PUBG API key 为什么报错”, even if the user does not mention the script name or CLI flags.
---

# PUBG Stats

Use this skill to run the local PUBG Steam stats query tool once and turn the result into a concise, accurate summary in the user's language.

## Goal

Transform a natural-language request into one local stats query, then explain what the numbers mean without inventing data.

## Resolve the script path

1. Prefer the bundled script at `scripts/query_stats.py` in this skill directory.
2. If it is unavailable, search the current workspace for `query_stats.py` or a README mentioning `PUBG Steam 战绩查询`.
3. Only use a discovered script after confirming it is the PUBG stats tool the user wants.
4. If no suitable local script exists, tell the user the local PUBG stats script is missing instead of guessing or fabricating results.
5. Keep the resolved path for command execution, but do not mention local absolute paths in the user-facing reply unless the user explicitly asks.

## Before running

1. Check whether `PUBG_API_KEY` is already set in the environment.
2. If it is not set, allow the local script to read `PUBG_API_KEY` from a `.env` file in the current working directory or the script directory.
3. If neither the environment nor `.env` provides the key, ask the user to run `! export PUBG_API_KEY='...'` in this session, or add `PUBG_API_KEY=...` to a local `.env` file. Do not ask them to paste the key into chat unless they explicitly want to.
4. Extract the Steam player name and the time window from the request.
5. If the request says `我`、`我的` or similar but does not actually include a Steam player name, ask a short follow-up for the player name.
6. If no time window is given, default to the last 3 days.
7. PUBG API usually exposes only about 14 days of recent match data. If the user asks for a longer range, cap it at 14 days and say so.

## Time window mapping

- `最近 N 天` → `--days N`
- `最近` / `近几天` / `这几天` → `--days 3`
- `最近一周` / `近 7 天` → `--days 7`
- `今天` / `昨天` / `前天` → convert to a concrete `YYYY-MM-DD` date based on the current Beijing date, then use `--date`
- A single date like `2026-05-05` → `--date 2026-05-05`
- A range like `2026-05-04 到 2026-05-07` → `--date 2026-05-04~2026-05-07`

When the user gives a relative phrase, resolve it in Beijing time before running the command. Treat date boundaries and displayed match times as Beijing time throughout. Only ask a follow-up question when the player name or intended date range is genuinely ambiguous.

## Command pattern

After resolving the script path, run:

```bash
python3 "<resolved-script-path>" --player "<player>" [--days N | --date YYYY-MM-DD | --date YYYY-MM-DD~YYYY-MM-DD]
```

Use shell quoting for player names. Run one command per request unless the user explicitly asks for a comparison across multiple players or windows.

## Response style

- Start with the answer, not the mechanics.
- Reply in the user's language.
- The final reply must always include both:
  1. a concise summary of sample size, time window, averages for kills, assists, damage, win rate, average rank, and the overall grade
  2. a battle record list based on the tool output
- For the battle record list, include each match as a compact item or table row using the factual fields returned by the tool, such as time, map, mode, kills, assists, damage, rank, and survival time.
- If there are many matches, keep the summary brief, but still include the battle record list rather than replacing it with prose only.
- Preserve factual metrics exactly as reported by the tool. Do not invent matches or claim values the tool did not return.
- Do not expose local absolute paths unless the user specifically asks where the script lives.
- Mention that this tool only supports Steam platform only when that limitation is relevant.

## Error handling

- Missing `PUBG_API_KEY` → tell the user how to export it in-session or place it in a local `.env` file
- `401` → API key is invalid or expired
- `404` or empty player lookup → player not found
- `429` → rate-limited, retry later
- No matches in the selected window → say there are no records in that period
- Invalid date format → show the expected `YYYY-MM-DD` or `YYYY-MM-DD~YYYY-MM-DD` format
- Missing local script → say the local PUBG stats tool could not be found
- Network failure → report the request failed; do not guess the result

## Examples

### Example 1
User: `查下 TGLTN 最近 7 天战绩`
Action: run with `--player "TGLTN" --days 7`

### Example 2
User: `看看我昨天打得怎么样，玩家名是 mySteamName`
Action: convert `昨天` to a concrete date and run with `--date YYYY-MM-DD`

### Example 3
User: `帮我看下最近表现`
Action: ask a short follow-up for the Steam player name, then default to the last 3 days if the user does not specify a window.

### Example 4
User: `帮我查 2026-05-04 到 2026-05-07 的 pubg 数据，玩家是 xxx`
Action: run with `--date 2026-05-04~2026-05-07`
