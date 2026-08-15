#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成打字机自我介绍卡片 SVG（GitHub 原生简洁风，日夜双主题）：
  assets/typing.svg       浅色
  assets/typing-dark.svg  深色（GitHub 夜间模式）

透明背景，直接坐在 GitHub 页面底色上（与贡献贪吃蛇同一设计语言）。
动效预算只有一个：逐字打字 → 停留 → 回删循环，配一根细竖线光标。
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

SANS = "-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif"

THEMES = {
    "": {"INK": "#1F2328", "ACC": "#1f883d"},            # 浅色（GitHub 日间）
    "-dark": {"INK": "#f0f6fc", "ACC": "#3fb950"},       # 深色（GitHub 夜间）
}

# 循环展示的句子
PHRASES = [
    "在杭州折腾 AI Infra 与 LLM",
    "具身智能爱好者 · bird-OS 孵化中",
    "每天刷一遍 GitHub 趋势",
]

W, H = 744, 72
FS = 17            # 字号
Y = 46             # 文字基线
CYCLE = 12         # 打字循环秒数
TYPE_D, HOLD_D, DEL_D = 0.36, 0.45, 0.15   # 打/停/删占本句时间片比重


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def char_w(ch):
    """无衬线字体近似宽度：CJK≈字号，ASCII≈字号*0.56"""
    return FS if ord(ch) > 0x2E7F else FS * 0.56


def build(t):
    ink, acc = t["INK"], t["ACC"]
    kf = ["@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}\n"]
    body = []

    n = len(PHRASES)
    slot = 100.0 / n
    for i, phrase in enumerate(PHRASES):
        a = i * slot
        chars = list(phrase)
        m = len(chars)
        total = sum(char_w(c) for c in chars)
        x = (W - total) / 2          # 每句各自居中
        t0 = a + slot * 0.05
        t1 = a + slot * TYPE_D
        d0 = a + slot * (TYPE_D + HOLD_D)
        d1 = a + slot * (TYPE_D + HOLD_D + DEL_D)
        for j, ch in enumerate(chars):
            on = t0 + (t1 - t0) * j / m
            off = d0 + (d1 - d0) * (m - j) / m
            kf.append(f"@keyframes c{i}_{j}{{0%,{on:.2f}%{{opacity:0}}"
                      f"{on + 0.01:.2f}%,{off:.2f}%{{opacity:1}}"
                      f"{off + 0.01:.2f}%,100%{{opacity:0}}}}\n")
            body.append(f'<text x="{x:.1f}" y="{Y}" font-family="{SANS}" font-size="{FS}" '
                        f'fill="{ink}" opacity="0" '
                        f'style="animation:c{i}_{j} {CYCLE}s linear infinite">{esc(ch)}</text>\n')
            x += char_w(ch)
        # 细竖线光标：贴本句末尾，仅本句时间片可见
        kf.append(f"@keyframes v{i}{{0%,{a:.2f}%{{visibility:hidden}}"
                  f"{a + 0.01:.2f}%,{d1:.2f}%{{visibility:visible}}"
                  f"{d1 + 0.01:.2f}%,100%{{visibility:hidden}}}}\n")
        body.append(f'<rect x="{x + 6:.1f}" y="{Y - FS + 4}" width="2" height="{FS}" fill="{acc}" '
                    f'style="animation:blink 1.1s steps(1) infinite,'
                    f'v{i} {CYCLE}s linear infinite"/>\n')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" role="img" aria-label="打字机自我介绍">\n'
            f'<style>\n{"".join(kf)}</style>\n'
            f'{"".join(body)}</svg>\n')


def main():
    os.makedirs(ASSETS, exist_ok=True)
    for suffix, t in THEMES.items():
        name = f"typing{suffix}.svg"
        with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
            f.write(build(t))
        print(f"生成 {name}")


if __name__ == "__main__":
    main()
