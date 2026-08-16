#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成极简高级风 hero banner（浅色 + 深色两版，呼吸光晕 + 流动细线）。
用法：python3 scripts/gen_banner.py
"""
import os
import random

W, H = 920, 300

THEMES = {
    "": {  # 浅色（GitHub 日间）
        "INK": "#1F2328", "DIM": "#656d76",
        "ACC": "#1f883d", "ACC2": "#2DA44E",
        "DOT_OPS": [0.10, 0.16, 0.22, 0.30], "ORB": ".10",
    },
    "-dark": {  # 深色（GitHub 夜间）
        "INK": "#f0f6fc", "DIM": "#8b949e",
        "ACC": "#3fb950", "ACC2": "#2ea043",
        "DOT_OPS": [0.05, 0.08, 0.12, 0.16], "ORB": ".16",
    },
}

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")


def build(T):
    INK, DIM, ACC = T["INK"], T["DIM"], T["ACC"]

    dots = []
    random.seed(42)
    for gx in range(24, W - 16, 48):
        for gy in range(24, H - 16, 48):
            jx, jy = random.randint(-3, 3), random.randint(-3, 3)
            r = random.choice([1, 1, 1, 1.5])
            o = random.choice(T["DOT_OPS"])
            dots.append(f'<circle cx="{gx+jx}" cy="{gy+jy}" r="{r}" fill="{INK}" opacity="{o}"/>')
    dots_svg = "\n  ".join(dots)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Jiahuo Lao - AI Infra, LLM, Agent, Embodied Intelligence">
<style>
  @keyframes breathe {{ 0%,100% {{ opacity:.32 }} 50% {{ opacity:.65 }} }}
  .glow   {{ animation: breathe 7s ease-in-out infinite }}
  .line   {{ stroke-dasharray: 6 10; animation: flow 14s linear infinite }}

  @keyframes flow {{ to {{ stroke-dashoffset: -320 }} }}
</style>
<defs>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{ACC}" stop-opacity="0"/>
    <stop offset=".5" stop-color="{ACC}" stop-opacity=".55"/>
    <stop offset="1" stop-color="{ACC}" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="orb" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="{ACC}" stop-opacity="{T['ORB']}"/>
    <stop offset="1" stop-color="{ACC}" stop-opacity="0"/>
  </radialGradient>
</defs>

<g>{dots_svg}</g>

<!-- 呼吸光晕（右上方） -->
<circle class="glow" cx="{W-190}" cy="74" r="150" fill="url(#orb)"/>

<!-- 流动光线（左侧竖向强调线） -->
<rect x="56" y="86" width="3" height="76" rx="1.5" fill="{ACC}"/>

<!-- 名字 -->
<text x="80" y="118" font-family="-apple-system, 'Segoe UI', 'PingFang SC', sans-serif"
      font-size="44" font-weight="700" letter-spacing=".5" fill="{INK}">Jiahuo Lao</text>
<text x="80" y="148" font-family="-apple-system, 'Segoe UI', 'PingFang SC', sans-serif"
      font-size="15" font-weight="500" fill="{DIM}">老家伙 · 杭州 · UTC+08:00</text>

<!-- 方向标签 -->
<text x="80" y="196" font-family="-apple-system, 'Segoe UI', 'PingFang SC', sans-serif"
      font-size="17" font-weight="500" letter-spacing="1" fill="{ACC}">AI Infra · LLM · Agent · 具身智能</text>

<!-- 底部流动细线 -->
<path class="line" d="M 56 246 H {W-56}" stroke="url(#edge)" stroke-width="1.5" fill="none"/>
<text x="{W-56}" y="236" text-anchor="end" font-family="-apple-system, 'Segoe UI', 'PingFang SC', sans-serif"
      font-size="11" fill="{DIM}" letter-spacing="2">TRAIN · SERVE · EMBODY</text>
</svg>'''


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    for suffix, T in THEMES.items():
        out = os.path.join(ASSETS, f"banner{suffix}.svg")
        with open(out, "w", encoding="utf-8") as f:
            f.write(build(T))
        print(f"生成 banner{suffix}.svg ({W}x{H})")
