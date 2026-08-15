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
    """返回 (总浏览, 总独立访客, [(日期, views, uniques)×14])"""
    if OFFLINE:
        import random
        rnd = random.Random(3)
        days = [(datetime(2026, 8, 1, tzinfo=timezone.utc) + timedelta(days=i))
                for i in range(N_BARS)]
        data = [(d.isoformat(), rnd.randint(1, 14), rnd.randint(1, 6)) for d in days]
        return sum(v for _, v, _ in data), sum(u for _, _, u in data), data
    req = urllib.request.Request(
        f"https://api.github.com/repos/{USER}/{USER}/traffic/views",
        headers={"User-Agent": "visitor-card-gen", "Accept": "application/vnd.github+json",
                 "Authorization": f"Bearer {TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        days = [(v["timestamp"][:10], v["count"], v["uniques"]) for v in d.get("views", [])]
        days = days[-N_BARS:]
        return d.get("count", 0), d.get("uniques", 0), days
    except Exception as e:
        print("traffic 获取失败，使用演示数据:", e, file=sys.stderr)
        return None, None, []


def build(pal, total, uniques, days):
    acc, ink, dim, dimmer = pal["ACC"], pal["INK"], pal["DIM"], pal["DIMMER"]
    track, div = pal["TRACK"], pal["DIV"]

    kf = ["@keyframes fadein{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}\n",
          "@keyframes pulse{0%,100%{opacity:.3}50%{opacity:1}}\n",
          "@keyframes rise{from{transform:scaleY(0)}}\n"]
    b = []

    # 无外框：透明背景，直接坐在 GitHub 页面底色上（与贪吃蛇一致）

    # 头部：LIVE 脉冲点 + 标题 + 右侧范围
    b.append(f'<circle cx="28" cy="{Y_HEAD - 4}" r="3" fill="{acc}" '
             f'style="animation:pulse 2s ease infinite"/>\n')
    b.append(f'<text x="40" y="{Y_HEAD}" font-family="{SANS}" font-size="12" '
             f'font-weight="600" fill="{ink}">访客统计</text>\n')
    b.append(f'<text x="110" y="{Y_HEAD}" font-family="{SANS}" font-size="11" '
             f'fill="{dimmer}">VISITORS</text>\n')
    b.append(f'<text x="{W - 26}" y="{Y_HEAD}" text-anchor="end" font-family="{SANS}" '
             f'font-size="11" fill="{dim}">近 14 天</text>\n')

    # 左列：大数字 + 说明
    demo = total is None
    b.append(f'<text x="26" y="{Y_NUM}" font-family="{SANS}" font-size="34" '
             f'font-weight="700" fill="{ink}" '
             f'style="animation:fadein .6s ease .2s both">'
             f'{"—" if demo else total}</text>\n')
    b.append(f'<text x="26" y="{Y_SUB}" font-family="{SANS}" font-size="12" fill="{dim}">'
             f'{"演示数据 · 等待 CI 首刷" if demo else f"次浏览 · {uniques} 位独立访客"}'
             f'</text>\n')

    # 分隔线 + 右列：每日趋势柱状图（逐根升起，今日高亮）
    b.append(f'<line x1="326" y1="24" x2="326" y2="{H - 30}" stroke="{div}"/>\n')
    if days:
        mx = max(v for _, v, _ in days) or 1
        bw, gap = 18, 8
        step = bw + gap
        chart_top = 44
        chart_h = Y_BASE - chart_top
        for i, (d, v, _u) in enumerate(days):
            h = max(3, v / mx * chart_h)
            x = CHART_X + i * step
            today = i == len(days) - 1
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
                 f'font-size="9" fill="{dimmer}">{days[0][0][5:]}</text>\n')
        b.append(f'<text x="{W - 26}" y="{Y_BASE + 16}" text-anchor="end" '
                 f'font-family="{SANS}" font-size="9" fill="{dimmer}">今天</text>\n')
    else:
        b.append(f'<text x="{CHART_X + 40}" y="{Y_BASE - 30}" font-family="{SANS}" '
                 f'font-size="10" fill="{dimmer}">等待数据 …</text>\n')

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
    total, uniques, days = fetch_views()
    for suffix, pal in PALETTES.items():
        name = f"visitors{suffix}.svg"
        with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
            f.write(build(pal, total, uniques, days))
        print(f"生成 {name}")


if __name__ == "__main__":
    main()
