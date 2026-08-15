#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成打字机自我介绍卡片 SVG（GitHub 原生简洁风，日夜双主题）：
  assets/typing.svg       浅色
  assets/typing-dark.svg  深色（GitHub 夜间模式）

透明背景，直接坐在 GitHub 页面底色上（与贡献贪吃蛇同一设计语言）。

排版方案（前端工程师视角的关键决策）：
逐字动画不用"每字一个 <text> 手算 x"——比例字体下每字符宽度差异巨大
（17px 时 I≈4px、M≈14px、空格≈4px），任何宽度估算都会导致间距错乱。
改为"前缀帧"：第 k 帧是完整 <text>（内容 = 句子前 k 字 + 光标），
由浏览器排版引擎自然布局，字符间距在任何平台/字体下都精确；
打字效果 = 每帧在自己的时间窗内可见（opacity 阶跃 keyframes）。
光标是帧内绿色 tspan（"|" 细竖线），自然跟随最后一个字符。
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
EPS = 0.01         # keyframes 阶跃偏移（%）

# 粗分字符宽度表（仅用于整行居中的起点估算，不影响字符间距——
# 间距由浏览器排版保证。估算误差 ±3% ≈ ±7px，肉眼不可辨）。
_NARROW = set("iljItf.,:;'|!()[]{}/\\ ")
_WIDE = set("mwMW@")


def est_w(s, fs):
    """估算字符串像素宽度（CJK=字号；ASCII 三档粗分）"""
    w = 0.0
    for ch in s:
        if ord(ch) > 0x2E7F:
            w += fs
        elif ch in _NARROW:
            w += fs * 0.31
        elif ch in _WIDE:
            w += fs * 0.88
        else:
            w += fs * 0.58
    return w


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(t):
    ink, acc = t["INK"], t["ACC"]
    kf = ["@keyframes caretblink{0%,49%{fill-opacity:1}50%,100%{fill-opacity:0}}\n"]
    body = []

    n = len(PHRASES)
    slot = 100.0 / n
    for i, phrase in enumerate(PHRASES):
        a = i * slot
        chars = list(phrase)
        m = len(chars)
        x0 = (W - est_w(phrase, FS)) / 2       # 整行居中（近似即可）

        # 本句时间片：短暂停顿 → 逐字打 → 停留 → 逐字回删 → 收尾空档
        t0 = a + slot * 0.05
        t1 = a + slot * TYPE_D
        d0 = a + slot * (TYPE_D + HOLD_D)
        d1 = a + slot * (TYPE_D + HOLD_D + DEL_D)

        # 第 k 帧可见窗口（%）：打字期 [on_k, on_{k+1})；满帧在停留期 [t1, d0)；
        # 回删期第 k 帧在 [d0+(d1-d0)(m-1-k)/m, 下一档) 内重现。
        def typing_on(k):
            return t0 + (t1 - t0) * k / m

        def del_on(k):
            return d0 + (d1 - d0) * (m - 1 - k) / m

        for k in range(m + 1):
            prefix = phrase[:k]
            if k < m:
                on1, off1 = typing_on(k), typing_on(k + 1)
                on2, off2 = del_on(k), del_on(k) + (d1 - d0) / m
                kf.append(
                    f"@keyframes f{i}_{k}{{0%,{on1:.2f}%{{opacity:0}}"
                    f"{on1 + EPS:.2f}%,{off1:.2f}%{{opacity:1}}"
                    f"{off1 + EPS:.2f}%,{on2:.2f}%{{opacity:0}}"
                    f"{on2 + EPS:.2f}%,{off2:.2f}%{{opacity:1}}"
                    f"{off2 + EPS:.2f}%,100%{{opacity:0}}}}\n")
            else:  # 满帧：打完即显示，停留到回删开始
                kf.append(
                    f"@keyframes f{i}_{k}{{0%,{t1:.2f}%{{opacity:0}}"
                    f"{t1 + EPS:.2f}%,{d0:.2f}%{{opacity:1}}"
                    f"{d0 + EPS:.2f}%,100%{{opacity:0}}}}\n")
            body.append(
                f'<text x="{x0:.1f}" y="{Y}" font-family="{SANS}" font-size="{FS}" '
                f'fill="{ink}" opacity="0" xml:space="preserve" '
                f'style="animation:f{i}_{k} {CYCLE}s linear infinite">'
                f'{esc(prefix)}'
                f'<tspan fill="{acc}" '
                f'style="animation:caretblink 1.1s steps(1) infinite">|</tspan>'
                f'</text>\n')

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
