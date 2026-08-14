#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「经典绿黑」终端窗口 SVG（带闪烁光标），用于 GitHub 主页。
用法：python3 scripts/gen_terminal_svgs.py
改完文案后重新运行，覆盖 assets/*.svg 即可。
"""
import os

W = 680          # 窗口宽度
TB = 34          # 标题栏高度
FONT = "Menlo, Consolas, 'Sarasa Mono SC', monospace"
FS = 13          # 字号
LH = 26          # 行间距
PAD = 20         # 左边距
TOP_B = 60       # 第一行文字的 baseline y

GREEN = "#4CAF50"   # 提示符
LIGHT = "#A5D6A7"   # 输出
DIM   = "#7DBB7D"   # 次要文字
BG1   = "#0C150C"   # 背景渐变上
BG2   = "#050A05"   # 背景渐变下
BAR   = "#162316"   # 标题栏

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def build(lines, title, out_name):
    total = len(lines)
    y = TOP_B
    y_last = TOP_B + total * LH          # 最后一个内容行的 baseline
    height = y_last + LH + 18            # 最后补一行提示符 + 底部留白
    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" role="img" aria-label="{esc(title)}">')
    parts.append('<style>@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.cur{animation:blink 1.1s steps(1) infinite}</style>')
    parts.append(f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG2}"/></linearGradient></defs>')
    parts.append(f'<rect width="{W}" height="{height}" rx="14" fill="url(#bg)"/>')
    parts.append(f'<rect width="{W}" height="{TB}" rx="14" fill="{BAR}"/>')
    parts.append(f'<rect y="{TB // 2}" width="{W}" height="{TB // 2}" fill="{BAR}"/>')
    parts.append(f'<circle cx="24" cy="{TB // 2}" r="6.5" fill="#FF5F57"/>')
    parts.append(f'<circle cx="48" cy="{TB // 2}" r="6.5" fill="#FEBC2E"/>')
    parts.append(f'<circle cx="72" cy="{TB // 2}" r="6.5" fill="#28C840"/>')
    parts.append(f'<text x="{W // 2}" y="22" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{DIM}">{esc(title)}</text>')
    for kind, text in lines:
        if kind == "blank":
            y += LH
            continue
        color = GREEN if kind == "prompt" else (LIGHT if kind == "out" else DIM)
        parts.append(f'<text x="{PAD}" y="{y}" font-family="{FONT}" font-size="{FS}" fill="{color}">{esc(text)}</text>')
        y += LH
    # 最后一行：提示符 + 闪烁块状光标（光标紧跟 "$ " 之后）
    parts.append(f'<text x="{PAD}" y="{y}" font-family="{FONT}" font-size="{FS}" fill="{GREEN}">~/laojiahuo2003 $</text>')
    parts.append(f'<rect class="cur" x="{PAD + 140}" y="{y - FS + 3}" width="9" height="{FS - 3}" fill="{GREEN}"/>')
    parts.append('</svg>')
    out = "\n".join(parts)
    path = os.path.join(ASSETS, out_name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"生成 {out_name}  ({height}px 高)")

# ---------- 内容定义 ----------
build(
    lines=[
        ("prompt", "~/laojiahuo2003 $ whoami"),
        ("out",    "▸ 老家伙 · 杭州 · 后端工程师 & AI 应用开发"),
        ("out",    "▸ 音乐 · 代码 · UTC+08:00"),
    ],
    title="老家伙 @ laojiahuo2003: ~",
    out_name="whoami.svg",
)

build(
    lines=[
        ("prompt", "~/laojiahuo2003 $ ls ./projects"),
        ("blank",  ""),
        ("out",    "  bird-OS      ★ 8   OS/系统  RISC-V 操作系统 · 大赛一等奖（2/240）"),
        ("out",    "  CXRAgent     ★ 8   AI/LLM   X光解读 · 多阶段推理 Agent"),
        ("out",    "  mini-chatgpt ★ 0   AI/LLM   大模型从 0 到 1 训练"),
        ("out",    "  BabyCode     ★ 2   AI/LLM   Python AI 编程助手 · Claude Code 灵感"),
        ("blank",  ""),
        ("prompt", "~/laojiahuo2003 $ cat ./awards.txt"),
        ("out",    "2024 全国大学生计算机系统能力大赛 · OS 原理赛道 · 华东区一等奖（2/240）"),
    ],
    title="老家伙 @ laojiahuo2003: ~/projects",
    out_name="projects.svg",
)

build(
    lines=[
        ("prompt", "~/laojiahuo2003 $ logout"),
        ("sep",    "────────────────────────────────────────────"),
        ("out",    "Write code, play music, repeat. — 老家伙"),
    ],
    title="老家伙 @ laojiahuo2003: ~",
    out_name="logout.svg",
)
