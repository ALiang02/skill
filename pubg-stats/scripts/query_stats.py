#!/usr/bin/env python3
"""PUBG Steam platform match stats query tool."""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

BASE_URL = "https://api.pubg.com/shards/steam"
BEIJING_TZ = timezone(timedelta(hours=8))

MAP_NAMES = {
    "Erangel_Main": "Erangel",
    "Desert_Main": "Miramar",
    "DihorOtok_Main": "Vikendi",
    "Savage_Main": "Sanhok",
    "Baltic_Main": "Taego",
    "Summerland_Main": "Karakin",
    "Tiger_Main": "Deston",
    "Neon_Main": "Neon",
    "Range_Main": "Camp",
}


def load_dotenv_key(dotenv_path):
    try:
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key.strip() != "PUBG_API_KEY":
                    continue
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                    value = value[1:-1]
                if value:
                    return value
    except OSError:
        return ""
    return ""


def get_api_key():
    key = os.environ.get("PUBG_API_KEY", "")
    if key:
        return key

    search_paths = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(__file__), ".env"),
    ]
    for dotenv_path in search_paths:
        key = load_dotenv_key(dotenv_path)
        if key:
            return key

    print("错误: 未设置 PUBG_API_KEY，且未在 .env 文件中找到该配置", file=sys.stderr)
    print("请运行: export PUBG_API_KEY='your-key-here'", file=sys.stderr)
    print("或在当前目录 / 脚本目录的 .env 中添加: PUBG_API_KEY=your-key-here", file=sys.stderr)
    sys.exit(1)


def api_request(url, api_key=None):
    headers = {
        "Accept": "application/vnd.api+json",
        "Accept-Encoding": "gzip",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                import gzip
                data = gzip.decompress(data)
            return json.loads(data.decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("错误: API Key 无效或已过期", file=sys.stderr)
        elif e.code == 404:
            print("错误: 未找到数据", file=sys.stderr)
        elif e.code == 429:
            print("错误: 请求过于频繁，请稍后重试", file=sys.stderr)
        else:
            print(f"错误: HTTP {e.code}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"错误: 网络连接失败 - {e.reason}", file=sys.stderr)
        sys.exit(1)


def get_player_matches(player_name, api_key):
    url = f"{BASE_URL}/players?filter[playerNames]={player_name}"
    data = api_request(url, api_key)

    players = data.get("data", [])
    if not players:
        print(f"错误: 未找到玩家 '{player_name}'", file=sys.stderr)
        sys.exit(1)

    player = players[0]
    match_refs = player.get("relationships", {}).get("matches", {}).get("data", [])
    return [m["id"] for m in match_refs]


def get_match_detail(match_id):
    url = f"{BASE_URL}/matches/{match_id}"
    return api_request(url)


def find_participant(included, player_name):
    for item in included:
        if item.get("type") != "participant":
            continue
        stats = item.get("attributes", {}).get("stats", {})
        if stats.get("name", "").lower() == player_name.lower():
            return stats
    return None


def format_duration(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def query_stats(player_name, cutoff, date_label, end_time=None):
    api_key = get_api_key()

    match_ids = get_player_matches(player_name, api_key)
    if not match_ids:
        print(f"玩家 {player_name} {date_label}没有比赛记录")
        return

    matches_data = []
    for mid in match_ids:
        detail = get_match_detail(mid)
        match_attrs = detail["data"]["attributes"]
        created_at = match_attrs.get("createdAt", "")

        try:
            match_time = datetime.fromisoformat(created_at.replace("Z", "+00:00")).astimezone(BEIJING_TZ)
        except (ValueError, AttributeError):
            continue

        if match_time < cutoff:
            continue

        if end_time and match_time >= end_time:
            continue

        included = detail.get("included", [])
        stats = find_participant(included, player_name)
        if not stats:
            continue

        matches_data.append({
            "time": match_time,
            "map": MAP_NAMES.get(match_attrs.get("mapName", ""), match_attrs.get("mapName", "")),
            "mode": match_attrs.get("gameMode", ""),
            "kills": stats.get("kills", 0),
            "assists": stats.get("assists", 0),
            "damage": stats.get("damageDealt", 0),
            "rank": stats.get("winPlace", 0),
            "survived": stats.get("timeSurvived", 0),
            "dbnos": stats.get("DBNOs", 0),
            "headshots": stats.get("headshotKills", 0),
            "heals": stats.get("heals", 0),
            "boosts": stats.get("boosts", 0),
            "walk_dist": stats.get("walkDistance", 0),
            "ride_dist": stats.get("rideDistance", 0),
        })

    if not matches_data:
        print(f"玩家 {player_name} {date_label}没有比赛记录")
        return

    # Sort by time descending
    matches_data.sort(key=lambda x: x["time"], reverse=True)

    # Output table
    print(f"=== {player_name} {date_label}战绩 (共 {len(matches_data)} 场) ===")
    print(f"{'时间(北京时间)':<12} | {'地图':<8} | {'模式':<10} | {'击杀':>4} | {'助攻':>4} | {'伤害':>7} | {'排名':>5} | {'存活时间':>8}")
    print("-" * 80)
    for m in matches_data:
        time_str = m["time"].strftime("%m-%d %H:%M")
        rank_str = f"#{m['rank']}" if m["rank"] else "N/A"
        print(f"{time_str:<12} | {m['map']:<8} | {m['mode']:<10} | {m['kills']:>4} | {m['assists']:>4} | {m['damage']:>7.1f} | {rank_str:>5} | {format_duration(m['survived']):>8}")

    # Summary
    total = len(matches_data)
    avg_kills = sum(m["kills"] for m in matches_data) / total
    avg_assists = sum(m["assists"] for m in matches_data) / total
    avg_damage = sum(m["damage"] for m in matches_data) / total
    avg_rank = sum(m["rank"] for m in matches_data if m["rank"]) / total
    wins = sum(1 for m in matches_data if m["rank"] == 1)
    win_rate = wins / total * 100

    print()
    print(f"汇总: 场均击杀 {avg_kills:.1f} | 场均助攻 {avg_assists:.1f} | 场均伤害 {avg_damage:.1f} | 吃鸡率 {win_rate:.0f}% | 平均排名 #{avg_rank:.1f}")

    # Rating
    print()
    if avg_kills >= 3 and avg_damage >= 300:
        combat = "高"
    elif avg_kills >= 1 and avg_damage >= 150:
        combat = "中"
    else:
        combat = "低"

    if avg_rank <= 10:
        survival = "强"
    elif avg_rank <= 30:
        survival = "中"
    else:
        survival = "弱"

    if avg_assists >= 2:
        teamplay = "优秀"
    elif avg_assists >= 1:
        teamplay = "良好"
    else:
        teamplay = "一般"

    score = 0
    if combat == "高": score += 3
    elif combat == "中": score += 2
    else: score += 1
    if survival == "强": score += 3
    elif survival == "中": score += 2
    else: score += 1
    if teamplay == "优秀": score += 3
    elif teamplay == "良好": score += 2
    else: score += 1
    if win_rate >= 20: score += 3
    elif win_rate >= 5: score += 2
    else: score += 1

    grades = {range(10, 13): "S", range(8, 10): "A", range(6, 8): "B", range(4, 6): "C"}
    grade = "D"
    for r, g in grades.items():
        if score in r:
            grade = g
            break

    print(f"评价: 击杀能力{combat} | 生存能力{survival} | 团队贡献{teamplay} | 综合评级 {grade}")


def main():
    parser = argparse.ArgumentParser(description="PUBG Steam 战绩查询")
    parser.add_argument("--player", required=True, help="玩家名称")
    parser.add_argument("--days", type=int, default=0, help="查询最近N天 (默认3, 最大14)")
    parser.add_argument("--date", type=str, default="", help="查询指定日期 (格式: 2026-05-05 或 2026-05-05~2026-05-07)")
    args = parser.parse_args()

    if args.date:
        # Parse date range in Beijing time: single date or date~date
        parts = args.date.split("~")
        try:
            start = datetime.strptime(parts[0].strip(), "%Y-%m-%d").replace(tzinfo=BEIJING_TZ)
            end = (start + timedelta(days=1) if len(parts) == 1
                   else datetime.strptime(parts[1].strip(), "%Y-%m-%d").replace(tzinfo=BEIJING_TZ) + timedelta(days=1))
        except ValueError:
            print("错误: 日期格式不正确，请使用 2026-05-05 或 2026-05-05~2026-05-07", file=sys.stderr)
            sys.exit(1)
        cutoff = start
        date_label = f"{args.date} (北京时间) "
    else:
        days = args.days if args.days > 0 else 3
        if days > 14:
            days = 14
            print("注意: PUBG API 数据仅保留14天，已自动调整为14天", file=sys.stderr)
        cutoff = datetime.now(BEIJING_TZ) - timedelta(days=days)
        date_label = f"近{days}天(按北京时间)"

    query_stats(args.player, cutoff, date_label, end_time=end if args.date else None)


if __name__ == "__main__":
    main()
