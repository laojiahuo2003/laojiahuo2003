#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「手记 Blog」小链接徽章（浅色 + 深色两版，箭头轻推 + 流动底线）。
风格与 banner 一致：GitHub 配色、SVG 内嵌 CSS 动画。
用法：python3 scripts/gen_blog_link.py
"""
import os

W, H = 560, 52

THEMES = {
    "": {  # 浅色（GitHub 日间）
        "INK": "#1F2328", "DIM": "#656d76",
        "ACC": "#1f883d",
    },
    "-dark": {  # 深色（GitHub 夜间）
        "INK": "#f0f6fc", "DIM": "#8b949e",
        "ACC": "#3fb950",
    },
}

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")


def build(T):
    INK, DIM, ACC = T["INK"], T["DIM"], T["ACC"]

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="手记 Blog - laojiahuo2003.github.io">
<style>
  @keyframes nudge {{ 0%, 100% {{ transform: translateX(0); opacity: .75 }} 50% {{ transform: translateX(5px); opacity: 1 }} }}
  @keyframes flow  {{ to {{ stroke-dashoffset: -320 }} }}
  .arrow {{ animation: nudge 2.4s ease-in-out infinite }}
  .line  {{ stroke-dasharray: 6 10; animation: flow 14s linear infinite }}
</style>
<defs>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{ACC}" stop-opacity="0"/>
    <stop offset=".5" stop-color="{ACC}" stop-opacity=".55"/>
    <stop offset="1" stop-color="{ACC}" stop-opacity="0"/>
  </linearGradient>
</defs>

<!-- 小书本图标 -->
<g transform="translate(84, 0)">
  <g stroke="{ACC}" stroke-width="1.8" stroke-linecap="round" fill="none">
    <path d="M 26 16 C 22 14, 18 14, 14 15.5 V 32 C 18 30.5, 22 30.5, 26 32"/>
    <path d="M 26 16 C 30 14, 34 14, 38 15.5 V 32 C 34 30.5, 30 30.5, 26 32 Z"/>
    <line x1="26" y1="16" x2="26" y2="32"/>
  </g>

  <!-- 文案 -->
  <text x="52" y="29" font-family="-apple-system, 'Segoe UI', 'PingFang SC', sans-serif"
        font-size="15" font-weight="600" letter-spacing="1" fill="{INK}">手记 Blog</text>
  <text x="146" y="29" font-family="ui-monospace, 'SF Mono', Menlo, Consolas, monospace"
        font-size="13" fill="{DIM}">laojiahuo2003.github.io</text>

  <!-- 箭头：周期性向右轻推 -->
  <g class="arrow">
    <line x1="330" y1="24" x2="344" y2="24" stroke="{ACC}" stroke-width="1.8" stroke-linecap="round"/>
    <path d="M 339 19 L 344 24 L 339 29" stroke="{ACC}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  </g>
</g>

<!-- 底部流动细线（与 banner 同款） -->
<path class="line" d="M 8 44 H {W-8}" stroke="url(#edge)" stroke-width="1.5" fill="none"/>
</svg>'''


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    for suffix, T in THEMES.items():
        out = os.path.join(ASSETS, f"blog-link{suffix}.svg")
        with open(out, "w", encoding="utf-8") as f:
            f.write(build(T))
        print(f"生成 blog-link{suffix}.svg ({W}x{H})")
