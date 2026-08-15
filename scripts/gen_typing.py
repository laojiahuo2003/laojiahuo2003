#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成打字机自我介绍卡片 SVG（绿黑终端风，日夜双主题）：
  assets/typing.svg       浅色
  assets/typing-dark.svg  深色（GitHub 夜间模式）

纯静态内容，无需 API，一次性生成即可。
动画机制：逐字符 opacity 阶梯（等宽字体按字符定位），
打字→停留→回删循环，兼容所有现代浏览器。
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

MONO = "Menlo, Consolas, 'Courier New', monospace"

PALETTES = {
    "": {   # 浅色（默认）
        "BG1": "#FAFDFA", "BG2": "#F0F8F0", "BORDER": "#D5E8D5", "BAR": "#E4F2E4",
        "GREEN": "#1A7F37", "LIGHT": "#1F2328", "DIM": "#4C7C54",
    },
    "-dark": {   # 深色（GitHub 夜间模式）
        "BG1": "#0C150C", "BG2": "#050A05", "BORDER": "#1E2B1E", "BAR": "#162316",
        "GREEN": "#3FB950", "LIGHT": "#A5D6A7", "DIM": "#7DBB7D",
    },
}

# 循环展示的句子
PHRASES = [
    "在杭州折腾 AI Infra 与 LLM",
    "具身智能爱好者 · bird-OS 孵化中",
    "每天刷一遍 GitHub 趋势",
]

FS = 15          # 打字行字号
X_TEXT = 26      # 打字行起点
Y_PROMPT = 82    # 提示行基线
Y_TYPE = 116     # 打字行基线
W, H = 744, 148
CYCLE = 12       # 一个完整循环的秒数

TYPE_D = 0.36    # 打字段占本句时间片的比重
HOLD_D = 0.45    # 停留段
DEL_D = 0.15     # 回删段


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def char_w(ch):
    """等宽字体近似宽度：CJK≈字号，ASCII≈字号*0.6"""
    return FS if ord(ch) > 0x2E7F else FS * 0.6


def build(pal):
    bg1, bg2, border, bar = pal["BG1"], pal["BG2"], pal["BORDER"], pal["BAR"]
    green, light, dim = pal["GREEN"], pal["LIGHT"], pal["DIM"]

    n = len(PHRASES)
    slot = 100.0 / n

    s = []
    s.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="打字机自我介绍">\n<style>\n'
    )
    s.append("@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}\n")

    # 每个字符一组关键帧：进入点=打字进度，退出点=回删进度（倒序删）
    for i, phrase in enumerate(PHRASES):
        a = i * slot
        chars = list(phrase)
        m = len(chars)
        t0 = a + slot * 0.05                      # 打字起点（留点停顿）
        t1 = a + slot * TYPE_D                    # 打字完成
        d0 = a + slot * (TYPE_D + HOLD_D)         # 回删起点
        d1 = a + slot * (TYPE_D + HOLD_D + DEL_D)  # 回删完成
        for j in range(m):
            on = t0 + (t1 - t0) * j / m
            off = d0 + (d1 - d0) * (m - j) / m
            s.append(f"@keyframes c{i}_{j}{{0%,{on:.2f}%{{opacity:0}}"
                     f"{on + 0.01:.2f}%,{off:.2f}%{{opacity:1}}"
                     f"{off + 0.01:.2f}%,100%{{opacity:0}}}}\n")
        # 光标可见时间片 = 本句打字+停留
        s.append(f"@keyframes v{i}{{0%,{a:.2f}%{{visibility:hidden}}"
                 f"{a + 0.01:.2f}%,{d1:.2f}%{{visibility:visible}}"
                 f"{d1 + 0.01:.2f}%,100%{{visibility:hidden}}}}\n")

    s.append("</style>\n")
    s.append(
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{bg1}"/><stop offset="1" stop-color="{bg2}"/>'
        f'</linearGradient></defs>\n'
    )
    # 终端窗口外框 + 标题栏 + 红黄绿三点
    s.append(f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)" stroke="{border}"/>\n')
    s.append(f'<rect width="{W}" height="34" rx="14" fill="{bar}"/>\n')
    s.append(f'<rect y="17" width="{W}" height="17" fill="{bar}"/>\n')
    s.append(f'<circle cx="24" cy="17" r="6.5" fill="#FF5F57"/>\n')
    s.append(f'<circle cx="48" cy="17" r="6.5" fill="#FEBC2E"/>\n')
    s.append(f'<circle cx="72" cy="17" r="6.5" fill="#28C840"/>\n')
    s.append(f'<text x="{W // 2}" y="22" text-anchor="middle" font-family="{MONO}" '
             f'font-size="12" fill="{dim}">老家伙 @ laojiahuo2003: ~/intro</text>\n')

    # 提示行
    s.append(f'<text x="{X_TEXT}" y="{Y_PROMPT}" font-family="{MONO}" '
             f'font-size="13" fill="{green}">~/laojiahuo2003 $ cat intro.txt</text>\n')

    # 打字行：每句按字符定位，逐个 opacity 进出
    for i, phrase in enumerate(PHRASES):
        x = float(X_TEXT)
        for j, ch in enumerate(phrase):
            s.append(f'<text x="{x:.0f}" y="{Y_TYPE}" font-family="{MONO}" '
                     f'font-size="{FS}" fill="{light}" opacity="0" '
                     f'style="animation:c{i}_{j} {CYCLE}s linear infinite">{esc(ch)}</text>\n')
            x += char_w(ch)
        # 光标：贴在本句末尾，仅本句时间片内可见，持续闪烁
        s.append(f'<rect x="{x + 7:.0f}" y="{Y_TYPE - FS + 2}" width="9" height="14" fill="{green}" '
                 f'style="animation:blink 1.1s steps(1) infinite, v{i} {CYCLE}s linear infinite"/>\n')

    s.append("</svg>\n")
    return "".join(s)


def main():
    os.makedirs(ASSETS, exist_ok=True)
    for suffix, pal in PALETTES.items():
        name = f"typing{suffix}.svg"
        with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
            f.write(build(pal))
        print(f"生成 {name}")


if __name__ == "__main__":
    main()
