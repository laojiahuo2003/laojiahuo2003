#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成杭州实时天气卡（日夜双主题）：
  assets/weather.svg       浅色
  assets/weather-dark.svg  深色（GitHub 夜间模式）

数据源：open-meteo.com Current Weather API（免费、无需 key）。
CI 每小时刷新一次；本地离线时回退演示数据。
文案随天气联动（下雨读 paper、高温空调房……）。
"""
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

SANS = "-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif"

PALETTES = {
    "": {"ACC": "#1f883d", "INK": "#1F2328", "DIM": "#656d76", "DIMMER": "#8c959f",
         "DIV": "#d8dee4"},
    "-dark": {"ACC": "#3fb950", "INK": "#f0f6fc", "DIM": "#8b949e", "DIMMER": "#6e7681",
              "DIV": "#30363d"},
}

LAT, LON = 30.2741, 120.1551   # 杭州
OFFLINE = os.environ.get("LIVE_OFFLINE") == "1"

W, H = 744, 124

# WMO weather code → (emoji, 中文描述)
WMO = {
    0: ("☀️", "晴"), 1: ("🌤️", "大致晴"), 2: ("⛅", "多云"), 3: ("☁️", "阴"),
    45: ("🌫️", "雾"), 48: ("🌫️", "雾凇"),
    51: ("🌦️", "毛毛雨"), 53: ("🌦️", "毛毛雨"), 55: ("🌦️", "毛毛雨"),
    61: ("🌧️", "小雨"), 63: ("🌧️", "中雨"), 65: ("🌧️", "大雨"),
    66: ("🌧️", "冻雨"), 67: ("🌧️", "冻雨"),
    71: ("🌨️", "小雪"), 73: ("🌨️", "中雪"), 75: ("❄️", "大雪"), 77: ("❄️", "雪粒"),
    80: ("🌦️", "阵雨"), 81: ("🌦️", "阵雨"), 82: ("⛈️", "强阵雨"),
    85: ("🌨️", "阵雪"), 86: ("🌨️", "阵雪"),
    95: ("⛈️", "雷暴"), 96: ("⛈️", "雷暴冰雹"), 99: ("⛈️", "雷暴冰雹"),
}


def caption(code, t, app):
    """随天气联动的一句话"""
    if code >= 95:
        return "雷雨天 · 先拔电源再写代码 ⚡"
    if 61 <= code <= 82 or 51 <= code <= 55:
        return "雨天适合读 paper ☔"
    if code >= 71:
        return "下雪了 · 去看一眼再回来 debug ❄️"
    if app >= 33:
        return "高温预警 · 空调房写代码效率 +20% 🥵"
    if app <= 5:
        return "天冷手冷 · 键盘敲慢一点 🧤"
    if code == 0 and 18 <= t <= 28:
        return "天气正好 · 出门走走再回来 debug 🌿"
    if 19 <= t <= 26:
        return "体感舒适 · 适合长时间心流 💚"
    return "平常的一天 · 平常地写两行代码 ☕"


def fetch():
    if OFFLINE:
        return {"temp": 31.2, "app": 33.4, "rh": 62, "code": 1, "wind": 11.3}
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
           f"&current=temperature_2m,apparent_temperature,relative_humidity_2m,"
           f"weather_code,wind_speed_10m&timezone=Asia%2FShanghai")
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            c = json.load(r)["current"]
        return {"temp": c["temperature_2m"], "app": c["apparent_temperature"],
                "rh": c["relative_humidity_2m"], "code": c["weather_code"],
                "wind": c["wind_speed_10m"]}
    except Exception as e:
        print("天气获取失败，使用演示数据:", e, file=sys.stderr)
        return {"temp": 31.2, "app": 33.4, "rh": 62, "code": 1, "wind": 11.3}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(pal, d):
    acc, ink, dim, dimmer, div = (pal[k] for k in ("ACC", "INK", "DIM", "DIMMER", "DIV"))
    emoji, desc = WMO.get(d["code"], ("🌡️", "未知天气"))
    quote = caption(d["code"], d["temp"], d["app"])

    b = ['<style>@keyframes pulse{0%,100%{opacity:.3}50%{opacity:1}}\n'
         '@keyframes fadein{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}\n</style>\n']

    # 头部：脉冲点 + 杭州 · 此刻 + 右侧 LIVE
    b.append(f'<circle cx="28" cy="25" r="3" fill="{acc}" style="animation:pulse 2s ease infinite"/>\n')
    b.append(f'<text x="40" y="29" font-family="{SANS}" font-size="12" font-weight="600" '
             f'fill="{ink}">杭州 · 此刻</text>\n')
    b.append(f'<text x="{W - 26}" y="29" text-anchor="end" font-family="{SANS}" font-size="10" '
             f'fill="{dimmer}">LIVE · 每小时刷新</text>\n')

    # 主体：emoji + 大温度 + 描述列
    b.append(f'<g style="animation:fadein .6s ease .1s backwards">\n')
    b.append(f'<text x="28" y="88" font-family="{SANS}" font-size="34">{emoji}</text>\n')
    b.append(f'<text x="86" y="90" font-family="{SANS}" font-size="34" font-weight="700" '
             f'fill="{ink}">{d["temp"]:.0f}°</text>\n')
    b.append(f'<text x="170" y="66" font-family="{SANS}" font-size="14" font-weight="600" '
             f'fill="{ink}">{esc(desc)}</text>\n')
    b.append(f'<text x="170" y="88" font-family="{SANS}" font-size="11" fill="{dim}">'
             f'体感 {d["app"]:.0f}° · 湿度 {d["rh"]:.0f}% · 风 {d["wind"]:.0f} km/h</text>\n')
    b.append('</g>\n')

    # 右列：联动文案
    b.append(f'<line x1="478" y1="46" x2="478" y2="{H - 30}" stroke="{div}"/>\n')
    b.append(f'<text x="502" y="64" font-family="{SANS}" font-size="12" fill="{acc}">'
             f'{esc(quote)}</text>\n')
    b.append(f'<text x="502" y="86" font-family="{SANS}" font-size="9" fill="{dimmer}">'
             f'data: open-meteo.com</text>\n')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" role="img" aria-label="杭州实时天气">\n'
            f'{"".join(b)}</svg>\n')


def main():
    os.makedirs(ASSETS, exist_ok=True)
    d = fetch()
    for suffix, pal in PALETTES.items():
        name = f"weather{suffix}.svg"
        with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
            f.write(build(pal, d))
        print(f"生成 {name}")


if __name__ == "__main__":
    main()
