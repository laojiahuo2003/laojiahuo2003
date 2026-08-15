#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成打字机自我介绍卡片 SVG（黑客终端风，日夜双主题，全特效）：
  assets/typing.svg       浅色
  assets/typing-dark.svg  深色（GitHub 夜间模式）

特效（纯 SVG+CSS，GitHub README 可播放）：
  · Matrix 数字雨背景（字符列下落 + 微光闪烁）
  · 开机引导序列：ssh 连接 → 认证 → 进度条
  · CRT 扫描线扫过
  · 逐字打字 → 停留 → 倒序回删循环
  · 打字完成瞬间 glitch 抖动
  · 辉光光标 + 底部 SESSION LIVE 状态栏

随机内容用固定种子，保证可复现。纯静态，无需 API。
"""
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

MONO = "Menlo, Consolas, 'Courier New', monospace"

PALETTES = {
    "": {   # 浅色（默认）
        "BG1": "#FAFDFA", "BG2": "#F0F8F0", "BORDER": "#D5E8D5", "BAR": "#E4F2E4",
        "GREEN": "#1A7F37", "LIGHT": "#1F2328", "DIM": "#4C7C54",
        "TRACK": "#E0EDE0", "DIV": "#CBE2CB",
        "RAIN": 0.10, "SCAN": 0.05,
    },
    "-dark": {   # 深色（GitHub 夜间模式）
        "BG1": "#0C150C", "BG2": "#050A05", "BORDER": "#1E2B1E", "BAR": "#162316",
        "GREEN": "#3FB950", "LIGHT": "#A5D6A7", "DIM": "#7DBB7D",
        "TRACK": "#12210F", "DIV": "#1E3A1E",
        "RAIN": 0.16, "SCAN": 0.09,
    },
}

# 循环展示的句子
PHRASES = [
    "在杭州折腾 AI Infra 与 LLM",
    "具身智能爱好者 · bird-OS 孵化中",
    "每天刷一遍 GitHub 趋势",
]

# 数字雨字符集：片假名 + 数字 + 符号，混一个"老家伙"彩蛋
RAIN_CHARS = "ｱｲｳｴｵｶｷｸｹｺ0123456789$#%&@+=<>*老家伙"

# 布局
W, H = 744, 240
FS = 15            # 打字行字号
X_TEXT = 26
Y_BOOT = [62, 84, 104]
Y_BAR_T, Y_PROMPT, Y_TYPE = 114, 152, 188
Y_STAT = 224
CYCLE = 12         # 打字循环秒数
TYPE_DELAY = 2.9   # 打字动画在开机序列之后启动

TYPE_D, HOLD_D, DEL_D = 0.36, 0.45, 0.15   # 打/停/删占本句时间片比重


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def char_w(ch):
    """等宽字体近似宽度：CJK≈字号，ASCII≈字号*0.6"""
    return FS if ord(ch) > 0x2E7F else FS * 0.6


def build(pal):
    rnd = random.Random(7)   # 固定种子：每次生成长得一样
    bg1, bg2, border, bar = pal["BG1"], pal["BG2"], pal["BORDER"], pal["BAR"]
    green, light, dim = pal["GREEN"], pal["LIGHT"], pal["DIM"]
    track, div, rain_a, scan_a = pal["TRACK"], pal["DIV"], pal["RAIN"], pal["SCAN"]

    n = len(PHRASES)
    slot = 100.0 / n
    kf = []
    body = []

    kf.append("@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}\n")
    kf.append("@keyframes fadein{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}\n")
    kf.append("@keyframes pulse{0%,100%{opacity:.3}50%{opacity:1}}\n")
    kf.append("@keyframes flick{0%,100%{opacity:.55}50%{opacity:1}}\n")
    kf.append("@keyframes scanmove{from{transform:translateY(-60px)}to{transform:translateY(" + str(H + 60) + "px)}}\n")

    # ---- 打字：逐字符 opacity 进出 + 光标时间片 + 完成瞬间 glitch ----
    for i, phrase in enumerate(PHRASES):
        a = i * slot
        chars = list(phrase)
        m = len(chars)
        t0 = a + slot * 0.05
        t1 = a + slot * TYPE_D
        d0 = a + slot * (TYPE_D + HOLD_D)
        d1 = a + slot * (TYPE_D + HOLD_D + DEL_D)
        for j in range(m):
            on = t0 + (t1 - t0) * j / m
            off = d0 + (d1 - d0) * (m - j) / m
            kf.append(f"@keyframes c{i}_{j}{{0%,{on:.2f}%{{opacity:0}}"
                      f"{on + 0.01:.2f}%,{off:.2f}%{{opacity:1}}"
                      f"{off + 0.01:.2f}%,100%{{opacity:0}}}}\n")
        kf.append(f"@keyframes v{i}{{0%,{a:.2f}%{{visibility:hidden}}"
                  f"{a + 0.01:.2f}%,{d1:.2f}%{{visibility:visible}}"
                  f"{d1 + 0.01:.2f}%,100%{{visibility:hidden}}}}\n")
        # glitch：打完的一瞬横向抖 + 闪烁
        g = t1
        kf.append(f"@keyframes g{i}{{0%,{g - 0.6:.2f}%{{transform:none;opacity:1}}"
                  f"{g - 0.45:.2f}%{{transform:translateX(2px);opacity:.55}}"
                  f"{g - 0.3:.2f}%{{transform:translateX(-2px)}}"
                  f"{g - 0.15:.2f}%{{transform:translateX(1px);opacity:.75}}"
                  f"{g:.2f}%{{transform:none;opacity:1}}100%{{transform:none}}}}\n")

    # ---- 背景层：数字雨 + 扫描线（先画，内容盖在上面）----
    # 数字雨：随机列，列内字符静态错落，整列下落循环 + 微光呼吸
    body.append('<clipPath id="card"><rect width="%d" height="%d" rx="14"/></clipPath>\n' % (W, H))
    body.append('<g clip-path="url(#card)">\n')
    x = 24.0
    col = 0
    while x < W - 20:
        n_chars = rnd.randint(9, 15)
        dur = rnd.uniform(6.5, 13.0)
        phase = rnd.uniform(0, 3)
        body.append(f'<g style="animation:rain{col} {dur:.1f}s linear infinite">\n')
        kf.append(f"@keyframes rain{col}{{from{{transform:translateY({-n_chars * 15 - 40:.0f}px)}}"
                  f"to{{transform:translateY({H + 20}px)}}}}\n")
        inner = f'<g style="animation:flick {rnd.uniform(2.4, 4.2):.1f}s ease-in-out {phase:.1f}s infinite">\n'
        yy = 0
        for k in range(n_chars):
            ch = rnd.choice(RAIN_CHARS)
            op = rain_a * rnd.uniform(0.35, 1.0)
            hot = k == n_chars - 2   # 亮头
            fill = light if hot else green
            o = min(1, rain_a * 3.2) if hot else op
            inner += (f'<text x="{x:.0f}" y="{yy:.0f}" font-family="{MONO}" font-size="11" '
                      f'fill="{fill}" opacity="{o:.2f}">{esc(ch)}</text>\n')
            yy += 15
        inner += "</g>\n"
        body.append(inner)
        body.append("</g>\n")
        x += rnd.uniform(42, 68)
        col += 1
    # CRT 扫描线：横向光带扫过
    body.append(f'<rect x="0" y="0" width="{W}" height="46" fill="{green}" opacity="{scan_a}" '
                f'style="animation:scanmove 6.5s linear infinite"/>\n')
    body.append("</g>\n")

    # ---- 卡片本体 ----
    body.append(
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{bg1}"/><stop offset="1" stop-color="{bg2}"/>'
        f'</linearGradient></defs>\n'
    )
    body.append(f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)" stroke="{border}"/>\n')
    # 标题栏 + 红黄绿三点
    body.append(f'<rect width="{W}" height="34" rx="14" fill="{bar}"/>\n')
    body.append(f'<rect y="17" width="{W}" height="17" fill="{bar}"/>\n')
    body.append('<circle cx="24" cy="17" r="6.5" fill="#FF5F57"/>\n')
    body.append('<circle cx="48" cy="17" r="6.5" fill="#FEBC2E"/>\n')
    body.append('<circle cx="72" cy="17" r="6.5" fill="#28C840"/>\n')
    body.append(f'<text x="{W // 2}" y="22" text-anchor="middle" font-family="{MONO}" '
                f'font-size="12" fill="{dim}">老家伙 @ laojiahuo2003: ~/intro</text>\n')

    # ---- 开机引导序列（一次性，按延迟依次浮现）----
    boots = [
        (0.15, "$ ssh visitor@laojiahuo2003", green),
        (0.55, "> connection established ✓", dim),
        (0.95, "> loading profile", dim),
    ]
    for (delay, text, color), y in zip(boots, Y_BOOT):
        body.append(f'<text x="{X_TEXT}" y="{y}" font-family="{MONO}" font-size="12" '
                    f'fill="{color}" opacity="0" '
                    f'style="animation:fadein .4s ease {delay}s both">{esc(text)}</text>\n')
    # 进度条：轨道 + 增长填充 + 百分比
    kf.append("@keyframes barw{to{width:240px}}\n")
    body.append(f'<rect x="{X_TEXT + 150}" y="{Y_BOOT[2] - 10}" width="240" height="8" '
                f'rx="4" fill="{track}" opacity="0" style="animation:fadein .4s ease .95s both"/>\n')
    body.append(f'<rect x="{X_TEXT + 150}" y="{Y_BOOT[2] - 10}" width="0" height="8" '
                f'rx="4" fill="{green}" '
                f'style="animation:barw 1.1s cubic-bezier(.2,.8,.2,1) 1.3s both,'
                f'fadein .4s ease .95s both"/>\n')
    body.append(f'<text x="{X_TEXT + 150 + 250}" y="{Y_BOOT[2] - 2}" font-family="{MONO}" '
                f'font-size="11" fill="{green}" opacity="0" '
                f'style="animation:fadein .3s ease 2.15s both">100%</text>\n')

    # ---- 提示行 ----
    body.append(f'<text x="{X_TEXT}" y="{Y_PROMPT}" font-family="{MONO}" '
                f'font-size="13" fill="{green}" opacity="0" '
                f'style="animation:fadein .4s ease 2.5s both">~/laojiahuo2003 $ cat intro.txt</text>\n')

    # ---- 打字行（延迟到开机序列后开始，无限循环）----
    for i, phrase in enumerate(PHRASES):
        xw = float(X_TEXT)
        body.append(f'<g style="animation:g{i} {CYCLE}s linear {TYPE_DELAY}s infinite;'
                    f'filter:drop-shadow(0 0 5px {green}55)">\n')
        for j, ch in enumerate(phrase):
            body.append(f'<text x="{xw:.0f}" y="{Y_TYPE}" font-family="{MONO}" '
                        f'font-size="{FS}" fill="{light}" opacity="0" '
                        f'style="animation:c{i}_{j} {CYCLE}s linear {TYPE_DELAY}s infinite">{esc(ch)}</text>\n')
            xw += char_w(ch)
        body.append("</g>\n")
        # 辉光光标：贴本句末尾，仅本句时间片可见
        body.append(f'<rect x="{xw + 7:.0f}" y="{Y_TYPE - FS + 2}" width="9" height="14" fill="{green}" '
                    f'style="filter:drop-shadow(0 0 4px {green});'
                    f'animation:blink 1.1s steps(1) infinite,'
                    f'v{i} {CYCLE}s linear {TYPE_DELAY}s infinite"/>\n')

    # ---- 底部状态栏 ----
    body.append(f'<line x1="16" y1="204" x2="{W - 16}" y2="204" stroke="{div}" stroke-dasharray="2 4"/>\n')
    body.append(f'<circle cx="30" cy="{Y_STAT - 4}" r="3" fill="{green}" '
                f'style="animation:pulse 2s ease infinite"/>\n')
    body.append(f'<text x="42" y="{Y_STAT}" font-family="{MONO}" font-size="10" '
                f'fill="{dim}">SESSION LIVE · 访问已记录</text>\n')
    body.append(f'<text x="{W - 22}" y="{Y_STAT}" text-anchor="end" font-family="{MONO}" '
                f'font-size="10" fill="{dim}">laojiahuo2003@github · TLS 1.3</text>\n')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" role="img" aria-label="打字机自我介绍">\n'
            f'<style>\n{"".join(kf)}</style>\n'
            f'{"".join(body)}</svg>\n')


def main():
    os.makedirs(ASSETS, exist_ok=True)
    for suffix, pal in PALETTES.items():
        name = f"typing{suffix}.svg"
        with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
            f.write(build(pal))
        print(f"生成 {name}")


if __name__ == "__main__":
    main()
