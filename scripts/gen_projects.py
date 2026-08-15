#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成项目精选卡片（浅色 + 深色两版）。
改项目列表：编辑下方 PROJECTS，然后 python3 scripts/gen_projects.py 并提交。
"""
import os

W = 744
ROW_H = 58
PAD_TOP = 26

PROJECTS = [
    # (名称, 描述, 右侧徽标)
    ("bird-OS",      "基于 xv6 的 RISC-V 操作系统",        "🏆 一等奖 2/240"),
    ("CXRAgent",     "胸部 X 光 · 多阶段推理 Agent",        "★ 8"),
    ("mini-chatgpt", "大模型从 0 到 1 训练的简单实现",      "LLM"),
    ("BabyCode",     "Claude Code 灵感的 AI 编程助手",      "★ 2"),
]

THEMES = {
    "": {   # 浅色（GitHub 日间）
        "BG1": "#ffffff", "BG2": "#f6f8fa", "BORDER": "#d0d7de",
        "GREEN": "#1f883d", "INK": "#1F2328", "DIM": "#656d76", "DIMMER": "#8c959f",
        "DASH": "#eaeef2",
    },
    "-dark": {   # 深色（GitHub 夜间）
        "BG1": "#0d1117", "BG2": "#0d1117", "BORDER": "#30363d",
        "GREEN": "#3fb950", "INK": "#f0f6fc", "DIM": "#8b949e", "DIMMER": "#6e7681",
        "DASH": "#21262d",
    },
}

FONT = "-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif"
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")


def txt(x, y, s, size, fill, weight=None, anchor=None):
    w = f' font-weight="{weight}"' if weight else ""
    a = f' text-anchor="{anchor}"' if anchor else ""
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'fill="{fill}"{w}{a}>{s}</text>\n')


def build(T):
    h = PAD_TOP + ROW_H * len(PROJECTS) + 10
    s = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="项目精选">\n'
        '<style>@keyframes fadein{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}</style>\n'
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{T["BG1"]}"/><stop offset="1" stop-color="{T["BG2"]}"/></linearGradient></defs>\n'
        f'<rect width="{W}" height="{h}" rx="8" fill="url(#bg)" stroke="{T["BORDER"]}"/>\n'
    )
    for i, (name, desc, badge) in enumerate(PROJECTS):
        y = PAD_TOP + ROW_H * i + ROW_H // 2 + 6
        s += f'<g style="animation:fadein .6s ease {0.1 + i * 0.15}s backwards">\n'
        s += f'<circle cx="34" cy="{y - 4}" r="3" fill="{T["GREEN"]}" opacity=".8"/>\n'
        s += txt(48, y, name, 14, T["INK"], weight="700")
        s += txt(190, y, desc, 11, T["DIM"])
        s += txt(W - 28, y, badge, 11, T["GREEN"], anchor="end")
        s += '</g>\n'
        if i < len(PROJECTS) - 1:
            ly = PAD_TOP + ROW_H * (i + 1)
            s += f'<line x1="28" y1="{ly}" x2="{W - 28}" y2="{ly}" stroke="{T["DASH"]}" stroke-dasharray="3 3"/>\n'
    s += "</svg>\n"
    return s


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    for suffix, T in THEMES.items():
        out = os.path.join(ASSETS, f"projects{suffix}.svg")
        with open(out, "w", encoding="utf-8") as f:
            f.write(build(T))
        print(f"生成 projects{suffix}.svg")
