#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成访客记录卡片 SVG（GitHub 原生简洁风，日夜双主题）：
  assets/visitors.svg       浅色
  assets/visitors-dark.svg  深色（GitHub 夜间模式）

数据源：GitHub Traffic API（/repos/{u}/{u}/traffic/views，需 administration
权限 token，Actions 中由 repo secret GH_PAT 提供；本地无 token 时回退演示数据）。

展示：近 14 天浏览次数 / 独立访客 / 每日趋势柱状图（今日高亮）。
设计：GitHub Primer 官方配色，白底净卡，动效仅保留柱状图升起 + LIVE 脉冲点。
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

USER = "laojiahuo2003"
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
DATA = os.path.join(HERE, "..", "data")
STORE = os.path.join(DATA, "visitors.json")   # 累计访客数据（GitHub Traffic 只保留 14 天，需自建持久化）

SANS = "-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif"

PALETTES = {
    "": {   # 浅色（GitHub 日间）
        "ACC": "#1f883d", "INK": "#1F2328", "DIM": "#656d76", "DIMMER": "#8c959f",
        "TRACK": "#eaeef2", "DIV": "#d8dee4",
    },
    "-dark": {   # 深色（GitHub 夜间）
        "ACC": "#3fb950", "INK": "#f0f6fc", "DIM": "#8b949e", "DIMMER": "#6e7681",
        "TRACK": "#21262d", "DIV": "#30363d",
    },
}

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
OFFLINE = os.environ.get("LIVE_OFFLINE") == "1"

W, H = 744, 150
Y_HEAD, Y_NUM, Y_SUB, Y_BASE, Y_FOOT = 34, 84, 108, 108, 138
CHART_X, N_BARS = 356, 14


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fetch_views():
    """返回 API 原始每日数据 [(date, views, uniques), ...]，失败返回 None（不是空列表，用于区分"接口挂了"与"真的没数据"）"""
    if OFFLINE:
        import random
        rnd = random.Random(3)
        days = [(datetime(2026, 8, 1, tzinfo=timezone.utc) + timedelta(days=i))
                for i in range(N_BARS)]
        return [(d.date().isoformat(), rnd.randint(1, 14), rnd.randint(1, 6)) for d in days]
    req = urllib.request.Request(
        f"https://api.github.com/repos/{USER}/{USER}/traffic/views",
        headers={"User-Agent": "visitor-card-gen", "Accept": "application/vnd.github+json",
                 "Authorization": f"Bearer {TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        return [(v["timestamp"][:10], int(v.get("count", 0)), int(v.get("uniques", 0)))
                for v in d.get("views", [])]
    except Exception as e:
        print("traffic 获取失败:", e, file=sys.stderr)
        return None


def load_store():
    """{date: {'views': int, 'uniques': int}}，文件不存在或损坏返回空 dict"""
    try:
        with open(STORE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {k: {"views": int(v["views"]), "uniques": int(v["uniques"])}
                for k, v in data.get("days", {}).items()}
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
        if not isinstance(e, FileNotFoundError):
            print("visitors.json 读取失败，重建:", e, file=sys.stderr)
        return {}


def save_store(days):
    os.makedirs(DATA, exist_ok=True)
    with open(STORE, "w", encoding="utf-8") as f:
        json.dump({
            "note": "累计访客数据。GitHub Traffic API 只保留 14 天，此文件由 CI 每小时合并入库以永久保留。",
            "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "days": {k: days[k] for k in sorted(days)},
        }, f, ensure_ascii=False, indent=2)


def merge(store, api_days):
    """对每一天取 API 与历史的 max（同一天 CI 多次跑不会回滚，14 天窗口内数据只增不减）"""
    for date, views, uniques in api_days:
        prev = store.get(date, {"views": 0, "uniques": 0})
        store[date] = {"views": max(prev["views"], views),
                       "uniques": max(prev["uniques"], uniques)}
    return store


def build(pal, total_views, total_uniques, recent_days, since):
    """total_* 为累计值，recent_days 为最近 N_BARS 天 [(date, views, uniques)]，since 是最早入库日期"""
    acc, ink, dim, dimmer = pal["ACC"], pal["INK"], pal["DIM"], pal["DIMMER"]
    track, div = pal["TRACK"], pal["DIV"]

    kf = ["@keyframes fadein{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}\n",
          "@keyframes pulse{0%,100%{opacity:.3}50%{opacity:1}}\n",
          "@keyframes rise{from{transform:scaleY(0)}}\n"]
    b = []

    # 头部：LIVE 脉冲点 + 标题 + 右侧"累计自 {since}"
    b.append(f'<circle cx="28" cy="{Y_HEAD - 4}" r="3" fill="{acc}" '
             f'style="animation:pulse 2s ease infinite"/>\n')
    b.append(f'<text x="40" y="{Y_HEAD}" font-family="{SANS}" font-size="12" '
             f'font-weight="600" fill="{ink}">访客统计</text>\n')
    b.append(f'<text x="110" y="{Y_HEAD}" font-family="{SANS}" font-size="11" '
             f'fill="{dimmer}">VISITORS</text>\n')
    range_label = f"累计自 {since}" if since else "累计"
    b.append(f'<text x="{W - 26}" y="{Y_HEAD}" text-anchor="end" font-family="{SANS}" '
             f'font-size="11" fill="{dim}">{range_label}</text>\n')

    # 左列：累计总浏览大数字 + 累计独立访客说明
    b.append(f'<text x="26" y="{Y_NUM}" font-family="{SANS}" font-size="34" '
             f'font-weight="700" fill="{ink}" '
             f'style="animation:fadein .6s ease .2s both">{total_views}</text>\n')
    b.append(f'<text x="26" y="{Y_SUB}" font-family="{SANS}" font-size="12" fill="{dim}">'
             f'次浏览 · 累计 {total_uniques} 位独立访客</text>\n')

    # 分隔线 + 右列：最近 14 天趋势柱状图（今日高亮）
    b.append(f'<line x1="326" y1="24" x2="326" y2="{H - 30}" stroke="{div}"/>\n')
    if recent_days:
        mx = max(v for _, v, _ in recent_days) or 1
        bw, gap = 18, 8
        step = bw + gap
        chart_top = 44
        chart_h = Y_BASE - chart_top
        for i, (d, v, _u) in enumerate(recent_days):
            h = max(3, v / mx * chart_h)
            x = CHART_X + i * step
            today = i == len(recent_days) - 1
            b.append(f'<rect x="{x}" y="{Y_BASE - h}" width="{bw}" height="{h:.0f}" rx="3" '
                     f'fill="{acc}" opacity="{1.0 if today else 0.35}" '
                     f'style="transform-box:fill-box;transform-origin:bottom;'
                     f'animation:rise .7s cubic-bezier(.2,.8,.2,1) {.15 + i * 0.05}s backwards"/>\n')
            if today:
                b.append(f'<text x="{x + bw / 2}" y="{Y_BASE - h - 6}" text-anchor="middle" '
                         f'font-family="{SANS}" font-size="9" fill="{acc}">今</text>\n')
        b.append(f'<line x1="{CHART_X}" y1="{Y_BASE}" x2="{W - 26}" y2="{Y_BASE}" '
                 f'stroke="{div}"/>\n')
        b.append(f'<text x="{CHART_X}" y="{Y_BASE + 16}" font-family="{SANS}" '
                 f'font-size="9" fill="{dimmer}">{recent_days[0][0][5:]}</text>\n')
        b.append(f'<text x="{W - 26}" y="{Y_BASE + 16}" text-anchor="end" '
                 f'font-family="{SANS}" font-size="9" fill="{dimmer}">今天</text>\n')
    else:
        b.append(f'<text x="{CHART_X + 40}" y="{Y_BASE - 30}" font-family="{SANS}" '
                 f'font-size="10" fill="{dimmer}">近 14 天暂无数据 …</text>\n')

    # 底部文案行
    b.append(f'<line x1="26" y1="{Y_FOOT - 16}" x2="{W - 26}" y2="{Y_FOOT - 16}" '
             f'stroke="{div}"/>\n')
    b.append(f'<text x="26" y="{Y_FOOT}" font-family="{SANS}" font-size="10" fill="{dim}">'
             f'▸ 每一次到访都被记录 · 感谢路过，欢迎常来 ✨</text>\n')
    b.append(f'<text x="{W - 26}" y="{Y_FOOT}" text-anchor="end" font-family="{SANS}" '
             f'font-size="10" fill="{dimmer}">powered by GitHub Insights</text>\n')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" role="img" aria-label="访客记录">\n'
            f'<style>\n{"".join(kf)}</style>\n{"".join(b)}</svg>\n')


def main():
    os.makedirs(ASSETS, exist_ok=True)
    api_days = fetch_views()

    # 接口失败：不动 store，不覆盖旧 SVG（除非首次跑）
    if api_days is None:
        for suffix in PALETTES:
            name = f"visitors{suffix}.svg"
            if os.path.exists(os.path.join(ASSETS, name)):
                print(f"跳过 {name}：Traffic 数据不可用，保留现有卡片")
        return

    store = load_store()
    store = merge(store, api_days)
    save_store(store)

    total_views = sum(v["views"] for v in store.values())
    total_uniques = sum(v["uniques"] for v in store.values())
    since = min(store) if store else ""

    # 最近 N_BARS 天柱状图数据（按日期排序，最后一根是今天）
    recent = [(d, store[d]["views"], store[d]["uniques"])
              for d in sorted(store)][-N_BARS:]

    for suffix, pal in PALETTES.items():
        name = f"visitors{suffix}.svg"
        with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
            f.write(build(pal, total_views, total_uniques, recent, since))
        print(f"生成 {name} (累计 {total_views} 次浏览 / {total_uniques} 位独立访客)")


if __name__ == "__main__":
    main()
