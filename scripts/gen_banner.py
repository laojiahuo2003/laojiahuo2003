#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成极简高级风 hero banner（深色卡片 + 呼吸光晕 + 流动光线）。
用法：python3 scripts/gen_banner.py
"""
import os

W, H = 920, 300
BG   = "#FBFDFB"   # 浅底（白底页面适配）
INK  = "#1F2328"   # 主文字
DIM  = "#57606A"   # 次文字
ACC  = "#1A7F37"   # 强调绿（GitHub green dark）
ACC2 = "#2DA44E"   # 深一档绿

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

dots = []
# 微妙点阵：网格抖动，营造质感
import random
random.seed(42)
for gx in range(24, W - 16, 48):
    for gy in range(24, H - 16, 48):
        jitter_x = random.randint(-3, 3)
        jitter_y = random.randint(-3, 3)
        r = random.choice([1, 1, 1, 1.5])
        o = random.choice([0.14, 0.20, 0.28, 0.36])
        dots.append(f'<circle cx="{gx+jitter_x}" cy="{gy+jitter_y}" r="{r}" fill="{INK}" opacity="{o}"/>')
dots_svg = "\n  ".join(dots)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Jiahuo Lao - AI Infra, LLM, Embodied Intelligence">
<style>
  @keyframes breathe {{ 0%,100% {{ opacity:.32 }} 50% {{ opacity:.65 }} }}
  .glow   {{ animation: breathe 7s ease-in-out infinite }}
  .line   {{ stroke-dasharray: 6 10 }}
  
</style>
<defs>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{ACC}" stop-opacity="0"/>
    <stop offset=".5" stop-color="{ACC}" stop-opacity=".55"/>
    <stop offset="1" stop-color="{ACC}" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="orb" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="{ACC}" stop-opacity=".14"/>
    <stop offset="1" stop-color="{ACC}" stop-opacity="0"/>
  </radialGradient>
</defs>

<rect width="{W}" height="{H}" rx="18" fill="{BG}" stroke="#D8E8D8"/>
<g class="dots">{dots_svg}</g>

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
<text x="80" y="196" font-family="Menlo, Consolas, monospace"
      font-size="17" font-weight="500" letter-spacing="1" fill="{ACC}">AI Infra · LLM · 具身智能</text>

<!-- 底部流动细线 -->
<path class="line" d="M 56 246 H {W-56}" stroke="url(#edge)" stroke-width="1.5" fill="none"/>
<text x="{W-56}" y="236" text-anchor="end" font-family="Menlo, Consolas, monospace"
      font-size="11" fill="{DIM}" letter-spacing="2">TRAIN · SERVE · EMBODY</text>
</svg>'''

path = os.path.join(ASSETS, "banner.svg")
with open(path, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"生成 banner.svg ({W}x{H})")
