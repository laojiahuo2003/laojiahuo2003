#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成作息分析卡（24 小时极坐标钟，日夜双主题）：
  assets/clock.svg       浅色
  assets/clock-dark.svg  深色（GitHub 夜间模式）

数据源：GitHub Events API（最近 ~300 条公开事件，约 90 天），
按北京时间（UTC+8）的小时统计"几点在 GitHub 上活动"。
透明背景、无外框，与贪吃蛇同一设计语言；动效：扇区逐时点亮 + 峰值脉冲。
"""
import json
import math
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
    },
    "-dark": {   # 深色（GitHub 夜间）
        "ACC": "#3fb950", "INK": "#f0f6fc", "DIM": "#8b949e", "DIMMER": "#6e7681",
    },
}

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
OFFLINE = os.environ.get("LIVE_OFFLINE") == "1"

W, H = 744, 210
CX, CY, R, SW = 116, 122, 54, 12       # 极坐标钟几何（钟心下移，刻度避开头部行）
GAP = 2.4                              # 扇区间留隙（度）
LR = R + SW / 2 + 13                   # 小时刻度标签半径
CST = timezone(timedelta(hours=8))     # 固定北京时间（CI 在 UTC 上跑，必须显式 +8）


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def demo_hours():
    counts = [0] * 24
    for h, c in [(0, 6), (1, 4), (2, 2), (9, 3), (10, 8), (11, 6), (14, 10),
                 (15, 13), (16, 9), (19, 8), (20, 12), (21, 16), (22, 21), (23, 17)]:
        counts[h] = c
    return counts, sum(counts)


def fetch_hours():
    """返回 [(hour, count)×24]，北京时间；失败/离线回退演示数据"""
    if OFFLINE:
        return demo_hours()
    counts = [0] * 24
    total = 0
    try:
        for page in (1, 2, 3):
            req = urllib.request.Request(
                f"https://api.github.com/users/{USER}/events/public?per_page=100&page={page}",
                headers={"User-Agent": "clock-card-gen", "Accept": "application/vnd.github+json",
                         **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
            with urllib.request.urlopen(req, timeout=30) as r:
                evs = json.load(r)
            if not evs:
                break
            for e in evs:
                if e["repo"]["name"] == f"{USER}/{USER}":
                    continue  # 过滤主页刷新机器人
                t = datetime.strptime(e["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                counts[t.astimezone(CST).hour] += 1
                total += 1
    except Exception as e:
        print("events 获取失败，使用演示数据:", e, file=sys.stderr)
        return demo_hours()
    if total == 0:
        return demo_hours()
    return counts, total


def polar(cx, cy, r, deg):
    a = math.radians(deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def sector(h):
    """第 h 小时的弧 path（顶=0 点，顺时针）"""
    a0 = h * 15 + GAP / 2 - 90
    a1 = (h + 1) * 15 - GAP / 2 - 90
    x0, y0 = polar(CX, CY, R, a0)
    x1, y1 = polar(CX, CY, R, a1)
    return f"M {x0:.1f} {y0:.1f} A {R} {R} 0 0 1 {x1:.1f} {y1:.1f}"


def build(pal, counts, total):
    acc, ink, dim, dimmer = pal["ACC"], pal["INK"], pal["DIM"], pal["DIMMER"]
    mx = max(counts) or 1
    peak = max(range(24), key=lambda h: counts[h])
    night = sum(counts[h] for h in list(range(22, 24)) + list(range(0, 6)))
    night_pct = night / total * 100 if total else 0
    # 黄金输出窗：连续 3 小时活动和最大的窗口
    win = max(range(24), key=lambda h: sum(counts[(h + i) % 24] for i in range(3)))
    buckets = [(0, 5, "凌晨型", "孤夜行者，太阳还没升代码先跑"), (6, 11, "上午型", "早鸟选手，思路跟着日出一块清晰"),
               (12, 17, "下午型", "稳定输出，午后是主战场"), (18, 23, "夜猫子", "夜深了，灵感才刚上班")]
    lo, hi, typ, verdict = max(buckets, key=lambda b: sum(counts[h] for h in range(b[0], b[1] + 1)))

    kf = ["@keyframes fadein{from{opacity:0}to{opacity:1}}\n",
          "@keyframes pulse{0%,100%{opacity:.4}50%{opacity:1}}\n"]
    b = []

    # 头部（与其他卡一致：脉冲点 + 标题 + 右侧范围）
    b.append(f'<circle cx="28" cy="41" r="3" fill="{acc}" style="animation:pulse 2s ease infinite"/>\n')
    b.append(f'<text x="40" y="45" font-family="{SANS}" font-size="15" font-weight="600" '
             f'fill="{ink}">作息分析</text>\n')
    b.append(f'<text x="128" y="45" font-family="{SANS}" font-size="11" fill="{dimmer}">ACTIVITY CLOCK</text>\n')
    b.append(f'<text x="{W - 26}" y="45" text-anchor="end" font-family="{SANS}" font-size="11" '
             f'fill="{dim}">近 90 天 · {total} 次活动</text>\n')

    # 极坐标钟：24 个小时扇区，透明度 = 活跃度（贡献热力图同款语言）
    for h in range(24):
        op = 0.14 + 0.86 * math.sqrt(counts[h] / mx) if mx else 0.14
        is_peak = h == peak
        anim = f'animation:pulse 2s ease infinite;' if is_peak else \
               f'animation:fadein .5s ease {0.15 + h * 0.04}s backwards;'
        b.append(f'<path d="{sector(h)}" fill="none" stroke="{acc}" stroke-width="{SW}" '
                 f'stroke-linecap="butt" opacity="{op:.2f}" style="{anim}"/>\n')

    # 小时刻度 6 / 12 / 18（外侧；顶部 0 点位不放标签，避免挤进头部行）
    for h, lab in [(6, "6点"), (12, "12点"), (18, "18点")]:
        lx, ly = polar(CX, CY, LR, h * 15 - 90)
        b.append(f'<text x="{lx:.1f}" y="{ly + 3:.1f}" text-anchor="middle" font-family="{SANS}" '
                 f'font-size="9" fill="{dimmer}">{lab}</text>\n')

    # 钟心：类型 + 峰值
    b.append(f'<text x="{CX}" y="{CY - 4}" text-anchor="middle" font-family="{SANS}" '
             f'font-size="15" font-weight="700" fill="{ink}">{typ}</text>\n')
    b.append(f'<text x="{CX}" y="{CY + 14}" text-anchor="middle" font-family="{SANS}" '
             f'font-size="9" fill="{dim}">{peak:02d}:00 最活跃</text>\n')

    # 右列：关键指标（标签左对齐，数值右对齐到卡片 padding，与 stats 卡同一栅格）
    rows = [
        ("峰值时段", f"{peak:02d}:00 – {peak:02d}:59"),
        ("黄金输出窗", f"{win:02d}:00 – {(win + 3) % 24:02d}:00"),
        ("夜猫子指数", f"{night_pct:.0f}%"),
        ("活动样本", f"{total} 次"),
    ]
    for i, (k, v) in enumerate(rows):
        y = 92 + i * 30
        b.append(f'<text x="262" y="{y}" font-family="{SANS}" font-size="12" fill="{dim}">{k}</text>\n')
        b.append(f'<text x="{W - 28}" y="{y}" text-anchor="end" font-family="{SANS}" font-size="13" '
                 f'font-weight="600" fill="{ink}">{v}</text>\n')

    # 底部一句评语
    b.append(f'<text x="262" y="{H - 24}" font-family="{SANS}" font-size="10" '
             f'fill="{dim}">“{verdict}”</text>\n')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" role="img" aria-label="作息分析">\n'
            f'<style>\n{"".join(kf)}</style>\n{"".join(b)}</svg>\n')


def main():
    os.makedirs(ASSETS, exist_ok=True)
    counts, total = fetch_hours()
    for suffix, pal in PALETTES.items():
        name = f"clock{suffix}.svg"
        with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
            f.write(build(pal, counts, total))
        print(f"生成 {name}")


if __name__ == "__main__":
    main()
