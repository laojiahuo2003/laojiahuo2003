#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成访客记录卡片 SVG（绿黑终端风，日夜双主题，带特效）：
  assets/visitors.svg       浅色
  assets/visitors-dark.svg  深色（GitHub 夜间模式）

数据源：GitHub Traffic API（/repos/{u}/{u}/traffic/views，需 push 权限 token，
Actions 中由 GITHUB_TOKEN 提供；本地无 token 时回退演示数据仅用于排版调试）。

展示：近 14 天浏览次数 / 独立访客 / 每日趋势柱状图（今日高亮），
特效：脉冲 LIVE 点、柱状图逐根升起、扫描线扫过。
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

USER = "laojiahuo2003"
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

MONO = "Menlo, Consolas, 'Courier New', monospace"

PALETTES = {
    "": {   # 浅色（默认）
        "BG1": "#FAFDFA", "BG2": "#F0F8F0", "BORDER": "#D5E8D5", "BAR": "#E4F2E4",
        "GREEN": "#1A7F37", "LIGHT": "#1F2328", "DIM": "#4C7C54", "DIMMER": "#7C9080",
        "TRACK": "#E0EDE0", "DIV": "#CBE2CB",
    },
    "-dark": {   # 深色（GitHub 夜间模式）
        "BG1": "#0C150C", "BG2": "#050A05", "BORDER": "#1E2B1E", "BAR": "#162316",
        "GREEN": "#3FB950", "LIGHT": "#A5D6A7", "DIM": "#7DBB7D", "DIMMER": "#5A7A5A",
        "TRACK": "#12210F", "DIV": "#1E3A1E",
    },
}

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
OFFLINE = os.environ.get("LIVE_OFFLINE") == "1"

W, H = 744, 168
Y_TITLE, Y_NUM, Y_SUB, Y_CHART_BASE, Y_FOOT = 58, 92, 112, 130, 152
CHART_X, CHART_W = 348, 356
N_BARS = 14


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
    bg1, bg2, border, bar = pal["BG1"], pal["BG2"], pal["BORDER"], pal["BAR"]
    green, light, dim, dimmer = pal["GREEN"], pal["LIGHT"], pal["DIM"], pal["DIMMER"]
    track, div = pal["TRACK"], pal["DIV"]

    kf = ["@keyframes fadein{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}\n",
          "@keyframes pulse{0%,100%{opacity:.3}50%{opacity:1}}\n",
          "@keyframes rise{from{transform:scaleY(0)}}\n",
          f"@keyframes scanmove{{from{{transform:translateY(-40px)}}to{{transform:translateY({H + 40}px)}}}}\n",
          "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}\n"]
    b = []

    # 卡片背景 + 扫描线（裁剪在卡片内）
    b.append(f'<clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath>\n')
    b.append(f'<g clip-path="url(#card)">')
    b.append(f'<rect x="0" y="0" width="{W}" height="30" fill="{green}" opacity="0.04" '
             f'style="animation:scanmove 6.5s linear infinite"/></g>\n')

    b.append(
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{bg1}"/><stop offset="1" stop-color="{bg2}"/>'
        f'</linearGradient></defs>\n')
    b.append(f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)" stroke="{border}"/>\n')

    # 标题栏 + 红黄绿三点
    b.append(f'<rect width="{W}" height="34" rx="14" fill="{bar}"/>\n')
    b.append(f'<rect y="17" width="{W}" height="17" fill="{bar}"/>\n')
    b.append('<circle cx="24" cy="17" r="6.5" fill="#FF5F57"/>\n')
    b.append('<circle cx="48" cy="17" r="6.5" fill="#FEBC2E"/>\n')
    b.append('<circle cx="72" cy="17" r="6.5" fill="#28C840"/>\n')
    b.append(f'<text x="{W // 2}" y="22" text-anchor="middle" font-family="{MONO}" '
             f'font-size="12" fill="{dim}">老家伙 @ laojiahuo2003: ~/visitor.log</text>\n')

    # 左列：LIVE 头 + 大数字 + 说明
    b.append(f'<circle cx="30" cy="{Y_TITLE - 4}" r="3" fill="{green}" '
             f'style="animation:pulse 2s ease infinite"/>\n')
    b.append(f'<text x="42" y="{Y_TITLE}" font-family="{MONO}" font-size="11" '
             f'fill="{dim}">VISITOR LOG · LIVE</text>\n')
    demo = total is None
    b.append(f'<text x="26" y="{Y_NUM}" font-family="{MONO}" font-size="30" font-weight="700" '
             f'fill="{light}" style="animation:fadein .6s ease .2s both">'
             f'{"—" if demo else total}</text>\n')
    b.append(f'<text x="26" y="{Y_SUB}" font-family="{MONO}" font-size="11" fill="{dim}">'
             f'{"演示数据 · 等待 CI 首刷" if demo else f"次浏览 · {uniques} 位独立访客 · 近 14 天"}'
             f'</text>\n')

    # 右列：14 天趋势柱状图（逐根升起，今日高亮）
    b.append(f'<text x="{CHART_X}" y="{Y_TITLE}" font-family="{MONO}" font-size="11" '
             f'fill="{dim}">DAILY VIEWS</text>\n')
    b.append(f'<line x1="{CHART_X}" y1="{Y_CHART_BASE}" x2="{W - 26}" y2="{Y_CHART_BASE}" '
             f'stroke="{div}" stroke-dasharray="2 4"/>\n')
    if days:
        mx = max(v for _, v, _ in days) or 1
        bw, gap = 18, 8
        step = bw + gap
        chart_h = Y_CHART_BASE - Y_TITLE - 14
        for i, (d, v, _u) in enumerate(days):
            h = max(3, v / mx * chart_h)
            x = CHART_X + i * step
            today = i == len(days) - 1
            b.append(f'<rect x="{x}" y="{Y_CHART_BASE - h}" width="{bw}" height="{h:.0f}" rx="3" '
                     f'fill="{green}" opacity="{1.0 if today else 0.55}" '
                     f'style="transform-box:fill-box;transform-origin:bottom;'
                     f'animation:rise .7s cubic-bezier(.2,.8,.2,1) {.15 + i * 0.05}s backwards"/>\n')
            if today:
                b.append(f'<text x="{x + bw / 2}" y="{Y_CHART_BASE - h - 6}" text-anchor="middle" '
                         f'font-family="{MONO}" font-size="9" fill="{green}">今</text>\n')
        b.append(f'<text x="{CHART_X}" y="{Y_CHART_BASE + 14}" font-family="{MONO}" '
                 f'font-size="9" fill="{dimmer}">{days[0][0][5:]}</text>\n')
        b.append(f'<text x="{W - 26}" y="{Y_CHART_BASE + 14}" text-anchor="end" '
                 f'font-family="{MONO}" font-size="9" fill="{dimmer}">今天</text>\n')
    else:
        b.append(f'<text x="{CHART_X + 40}" y="{Y_CHART_BASE - 30}" font-family="{MONO}" '
                 f'font-size="10" fill="{dimmer}">等待数据 …</text>\n')

    # 底部文案行（用户要求加的文字）
    b.append(f'<line x1="16" y1="{Y_FOOT - 14}" x2="{W - 16}" y2="{Y_FOOT - 14}" '
             f'stroke="{div}" stroke-dasharray="2 4"/>\n')
    b.append(f'<text x="26" y="{Y_FOOT}" font-family="{MONO}" font-size="10" fill="{dim}">'
             f'▸ 每一次到访都被记录 · 感谢路过，欢迎常来 ✨</text>\n')
    b.append(f'<rect x="604" y="{Y_FOOT - 9}" width="7" height="10" fill="{green}" '
             f'style="animation:blink 1.1s steps(1) infinite"/>\n')
    b.append(f'<text x="{W - 22}" y="{Y_FOOT}" text-anchor="end" font-family="{MONO}" '
             f'font-size="10" fill="{dim}">powered by GitHub Insights</text>\n')

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
