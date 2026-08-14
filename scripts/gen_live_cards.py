#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成主页三张实时卡片 SVG（绿黑终端风，内嵌 CSS 动画）：
  assets/journey.svg  足迹条（加入年份 / 最近活动 / streak）
  assets/picks.svg    每日精选（Top5 + 今日扫描 + 语言分布）
  assets/stats.svg    统计 neofetch（stars/commits/repos/followers）

数据源：GitHub REST/GraphQL API + github-daily-report 仓库
环境变量 GH_TOKEN 可选（Actions 中传入以提升 API 限额）
LIVE_OFFLINE=1 时用演示数据，仅用于本地排版调试
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

USER = "laojiahuo2003"
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
REPORT_REPO = "https://github.com/laojiahuo2003/github-daily-report.git"

MONO = "Menlo, Consolas, 'Courier New', monospace"
# 颜色常量由 PALETTES 在 main() 中按主题注入
INK = TRACK = DIV = PILL = DDOT = DASH = ""
BG1 = BG2 = BORDER = ""
GREEN = LIGHT = DIM = DIMMER = ""

PALETTES = {
    "": {   # 浅色（默认）
        "BG1": "#FAFDFA", "BG2": "#F0F8F0", "BORDER": "#D5E8D5",
        "GREEN": "#1A7F37", "LIGHT": "#1F2328", "DIM": "#4C7C54", "DIMMER": "#7C9080",
        "INK": "#1F2328", "TRACK": "#E0EDE0", "DIV": "#CBE2CB", "PILL": "#BFDDBF",
        "DDOT": "#A8C8A8", "DASH": "#D5E8D5",
    },
    "-dark": {   # 深色（GitHub 夜间模式）
        "BG1": "#0C150C", "BG2": "#050A05", "BORDER": "#1E2B1E",
        "GREEN": "#3FB950", "LIGHT": "#A5D6A7", "DIM": "#7DBB7D", "DIMMER": "#5A7A5A",
        "INK": "#E6EDF3", "TRACK": "#12210F", "DIV": "#1E3A1E", "PILL": "#234923",
        "DDOT": "#2A4A2A", "DASH": "#1A2A1A",
    },
}

OFFLINE = os.environ.get("LIVE_OFFLINE") == "1"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def api(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "profile-card-gen",
        "Accept": "application/vnd.github+json",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def graphql(query):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"User-Agent": "profile-card-gen", "Content-Type": "application/json",
                 **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


# ---------------- 数据获取 ----------------

def fetch_user():
    if OFFLINE:
        return {"created_at": "2020-05-01T00:00:00Z", "followers": 3, "public_repos": 16}
    return api(f"https://api.github.com/users/{USER}")


def fetch_stars():
    """全部公开仓库的 star 总数"""
    if OFFLINE:
        return 36
    try:
        repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100")
        return sum(r.get("stargazers_count", 0) for r in repos)
    except Exception as e:
        print("stars 获取失败:", e, file=sys.stderr)
        return None


def fetch_events():
    if OFFLINE:
        return [
            {"type": "PushEvent", "repo": "laojiahuo2003/CXRAgent", "created_at": "2026-08-14T07:00:00Z", "n": 3},
            {"type": "WatchEvent", "repo": "anthropics/skills", "created_at": "2026-08-14T04:00:00Z"},
            {"type": "PushEvent", "repo": "laojiahuo2003/github-daily-report", "created_at": "2026-08-13T09:00:00Z", "n": 1},
        ]
    evs = api(f"https://api.github.com/users/{USER}/events/public?per_page=100")
    out, seen = [], set()
    for e in evs:
        if e["repo"]["name"] == f"{USER}/{USER}":
            continue  # 过滤主页刷新机器人的提交
        key = (e["type"], e["repo"]["name"])
        if key in seen:
            continue
        seen.add(key)
        t, p = e["type"], e.get("payload", {})
        repo, at = e["repo"]["name"], e["created_at"]
        if t == "PushEvent":
            out.append({"type": "push", "repo": repo, "created_at": at,
                        "detail": f"{len(p.get('commits', []))} commits"})
        elif t == "PullRequestEvent":
            title = p.get("pull_request", {}).get("title", "")
            out.append({"type": "PR", "repo": repo, "created_at": at,
                        "detail": title or p.get("action", "")})
        elif t == "IssuesEvent":
            title = p.get("issue", {}).get("title", "")
            out.append({"type": "issue", "repo": repo, "created_at": at,
                        "detail": title or p.get("action", "")})
        elif t == "WatchEvent":
            out.append({"type": "star", "repo": repo, "created_at": at, "detail": ""})
        elif t == "ForkEvent":
            out.append({"type": "fork", "repo": repo, "created_at": at, "detail": ""})
        elif t == "ReleaseEvent":
            name = p.get("release", {}).get("name") or p.get("release", {}).get("tag_name", "")
            out.append({"type": "release", "repo": repo, "created_at": at, "detail": name})
        elif t == "CreateEvent":
            out.append({"type": "create", "repo": repo, "created_at": at,
                        "detail": p.get("ref_type", "")})
        if len(out) >= 5:
            break
    return out


def fetch_contributions():
    """年度提交 + streak（需 token；失败则回退）"""
    if OFFLINE:
        return {"year_total": 523, "streak": 12, "longest": 47}
    if not TOKEN:
        return {"year_total": None, "streak": None, "longest": None}
    q = """query {
      user(login: "%s") {
        contributionsCollection {
          contributionCalendar { totalContributions
            weeks { contributionDays { contributionCount } } }
        }
      }
    }""" % USER
    try:
        data = graphql(q)["data"]["user"]["contributionsCollection"]
        days = [d["contributionCount"] for w in data["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
        year_total = data["contributionCalendar"]["totalContributions"]
        streak = 0
        for c in reversed(days):
            if c > 0:
                streak += 1
            elif streak > 0:
                break
        longest = cur = 0
        for c in days:
            cur = cur + 1 if c > 0 else 0
            longest = max(longest, cur)
        return {"year_total": year_total, "streak": streak, "longest": longest}
    except Exception as e:
        print("contributions 获取失败:", e, file=sys.stderr)
        return {"year_total": None, "streak": None, "longest": None}


def fetch_report():
    """克隆日报仓库，返回（日期, top5 列表, 新发现数, 增长数, 语言分布 dict）"""
    tmp = "/tmp/live-report"
    subprocess.run(["rm", "-rf", tmp], check=False)
    r = subprocess.run(["git", "clone", "--quiet", "--depth", "1", REPORT_REPO, tmp],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("克隆报告仓库失败:", r.stderr, file=sys.stderr)
        return None
    rdir = os.path.join(tmp, "reports")
    files = sorted(f for f in os.listdir(rdir) if f.endswith(".md"))
    if not files:
        return None
    content = open(os.path.join(rdir, files[-1]), encoding="utf-8").read()
    m = re.match(r"# GitHub 每日报告 - (\S+)", content)
    hm = re.match(r"(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})", files[-1])
    if hm:
        date_str = f"{hm.group(1)} {hm.group(2)}:{hm.group(3)}"
    else:
        date_str = m.group(1) if m else files[-1][:10]

    sec = re.search(r"## ✨ 新发现项目(.*?)(?=\n## |\Z)", content, re.S)
    entries = []
    langs = {}
    if sec:
        for mm in re.finditer(r"- \*\*\[([^\]]+)\]\(([^)]+)\)\*\* ⭐(\d+)(?:[^\n]*?) `(\S+)`", sec.group(1)):
            name, url, stars, lang = mm.group(1), mm.group(2), int(mm.group(3)), mm.group(4)
            entries.append((name, url, stars, lang))
            langs[lang] = langs.get(lang, 0) + 1
    fast = len(re.findall(r"^\d+\. \*\*\[", content, re.M))
    return {"date": date_str, "top": entries[:5], "new": len(entries), "fast": fast, "langs": langs}


def rel_time(iso):
    dt = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    s = int((datetime.now(timezone.utc) - dt).total_seconds())
    if s < 3600:
        return f"{max(1, s // 60)}m"
    if s < 86400:
        return f"{s // 3600}h"
    return f"{s // 86400}d"


def fmt_k(n):
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


# ---------------- SVG 组件 ----------------

def svg_open(w, h, label):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">\n'
        '<style>\n'
        "@keyframes breathe{0%,100%{opacity:.4}50%{opacity:.9}}\n"
        "@keyframes pulse{0%,100%{opacity:.3}50%{opacity:1}}\n"
        "@keyframes eq{0%,100%{transform:scaleY(.4)}50%{transform:scaleY(1)}}\n"
        "@keyframes fadein{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}\n"
        "@keyframes grow{from{width:0}}\n"
        "@keyframes ringdraw{from{stroke-dashoffset:138}}\n"
        "@keyframes flick{0%,100%{transform:scale(1)}30%{transform:scale(1.15)}60%{transform:scale(.95)}}\n"
        "@keyframes scan{0%{opacity:.06}100%{opacity:.06}}\n"
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}\n"
        ".pulse{animation:pulse 2s ease infinite}\n"
        ".flick{animation:flick 1.8s ease-in-out infinite;transform-origin:center}\n"
        "</style>\n"
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG2}"/></linearGradient></defs>\n'
        f'<rect width="{w}" height="{h}" rx="14" fill="url(#bg)" stroke="{BORDER}"/>\n'
    )


def txt(x, y, s, size=12, fill=None, mono=True, weight=None, extra=""):
    fill = LIGHT if fill is None else fill
    fam = MONO if mono else "-apple-system,'Segoe UI','PingFang SC',sans-serif"
    wattr = f' font-weight="{weight}"' if weight else ""
    return (f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" '
            f'fill="{fill}"{wattr}{extra}>{esc(s)}</text>\n')


def build_journey(user, events, contrib):
    W, H = 744, 186
    s = svg_open(W, H, "足迹条")
    # 年份环
    year = user["created_at"][:4]
    nth = datetime.now(timezone.utc).year - int(year) + 1
    frac = (datetime.now(timezone.utc).timetuple().tm_yday) / 366
    C = 138
    s += f'<circle cx="62" cy="62" r="22" fill="none" stroke="{TRACK}" stroke-width="5"/>\n'
    s += (f'<circle cx="62" cy="62" r="22" fill="none" stroke="{GREEN}" stroke-width="5" '
          f'stroke-linecap="round" stroke-dasharray="{C}" stroke-dashoffset="{C*(1-frac):.0f}" '
          f'style="animation:ringdraw 1.6s cubic-bezier(.2,.8,.2,1) backwards"/>\n')
    s += txt(62, 66, f"{nth}th", 10, DIM, extra=' text-anchor="middle"')
    s += txt(100, 58, year, 28, INK, weight="700")
    s += txt(100, 78, f"GITHUBING SINCE · 第 {nth} 年", 9, DIM)
    # 分隔线
    s += f'<line x1="290" y1="20" x2="290" y2="{H-20}" stroke="{DIV}" stroke-dasharray="2 4"/>\n'
    # 最近活动
    s += txt(312, 34, "◉ 最近活动 · LIVE", 10, DIM)
    s += f'<circle cx="318" cy="48" r="3" fill="{GREEN}" class="pulse"/>\n'
    y = 54
    for i, e in enumerate(events[:5]):
        t = e.get("_rel") or rel_time(e["created_at"])
        ty = e["type"]
        name = e["repo"].split("/", 1)[-1] if e["repo"].startswith(f"{USER}/") else e["repo"]
        det = e.get("detail") or ""
        if det:
            det = " · " + det
        detail = f"{name}{det}"
        if len(detail) > 24:
            detail = detail[:23] + "…"
        y += 22
        s += txt(312, y, t, 10, DIMMER)
        if i == 0:
            s += f'<circle cx="352" cy="{y-3}" r="3" fill="{GREEN}" class="pulse"/>\n'
        else:
            s += f'<circle cx="352" cy="{y-3}" r="3" fill="{DDOT}"/>\n'
        s += txt(364, y, ty, 10, DIM)
        s += txt(418, y, detail, 11, LIGHT)
    # streak
    s += f'<line x1="574" y1="20" x2="574" y2="{H-20}" stroke="{DIV}" stroke-dasharray="2 4"/>\n'
    s += txt(598, 34, "STREAK", 10, DIM)
    st = contrib["streak"]
    if st is not None:
        s += f'<text x="598" y="72" font-size="24" class="flick">🔥</text>\n'
        s += txt(634, 70, f"{st} 天", 22, LIGHT, weight="700")
        if contrib["longest"]:
            s += txt(598, 92, f"连续贡献 · 最长 {contrib['longest']} 天", 9, DIMMER)
    else:
        s += txt(598, 66, "🚀", 24)
        s += txt(634, 64, "keep", 20, LIGHT, weight="700")
        s += txt(598, 90, "coding every day", 9, DIMMER)
    s += "</svg>\n"
    return s


def build_picks(rep):
    W, H = 744, 316
    s = svg_open(W, H, "每日精选")
    # 头部
    for i, (h, d) in enumerate([(8, 0), (14, -.3), (6, -.6), (12, -.15), (9, -.45)]):
        s += (f'<rect x="{28 + i*6}" y="34" width="3" height="{h}" rx="1" fill="{GREEN}" '
              f'style="transform-origin:{29.5 + i*6}px 38px;animation:eq 1.2s ease {d}s infinite"/>\n')
    s += txt(66, 44, "GitHub 趋势雷达", 14, LIGHT, weight="600")
    s += f'<rect x="216" y="30" width="46" height="16" rx="8" fill="none" stroke="{GREEN}"/>\n'
    s += f'<circle cx="228" cy="38" r="2.5" fill="{GREEN}" class="pulse"/>\n'
    s += txt(235, 42, "LIVE", 9, GREEN)
    s += txt(W - 28, 42, f"{rep['date']} 09:36", 10, DIM, extra=' text-anchor="end"')
    # 左列 Top5
    y = 78
    for i, (name, url, stars, lang) in enumerate(rep["top"]):
        y += 36
        s += f'<g style="animation:fadein .6s ease {.1 + i*.15}s backwards">\n'
        s += txt(28, y, f"{i+1:02d}", 11, GREEN)
        disp = name if len(name) <= 34 else name[:33] + "…"
        s += txt(56, y, disp, 13, INK)
        s += txt(416, y, f"▲ {fmt_k(stars)}", 11, GREEN)
        lw = max(44, len(lang) * 6 + 16)
        s += f'<rect x="{W - 28 - lw}" y="{y-13}" width="{lw}" height="17" rx="9" fill="none" stroke="{PILL}"/>\n'
        s += txt(W - 28 - lw / 2, y, lang, 9, DIM, extra=' text-anchor="middle"')
        s += '</g>\n'
        if i < len(rep["top"]) - 1:
            s += f'<line x1="28" y1="{y + 12}" x2="440" y2="{y + 12}" stroke="{DASH}" stroke-dasharray="3 3"/>\n'
    # 右列
    XR = 486
    s += f'<line x1="458" y1="24" x2="458" y2="{H-24}" stroke="{DIV}" stroke-dasharray="2 4"/>\n'
    s += txt(XR, 66, "今日扫描", 10, DIM)
    for i, (num, lab) in enumerate([(rep["new"], "新发现"), (rep["fast"], "增长追踪")]):
        x = XR + i * 100
        s += txt(x, 92, str(num), 20, LIGHT, weight="700")
        s += txt(x, 106, lab, 9, DIMMER)
    s += txt(XR, 134, "语言分布", 10, DIM)
    langs = sorted(rep["langs"].items(), key=lambda kv: -kv[1])[:3]
    total = sum(rep["langs"].values()) or 1
    for i, (lang, cnt) in enumerate(langs):
        y = 150 + i * 20
        pct = cnt / total * 100
        lbl = lang if len(lang) <= 10 else lang[:9] + "…"
        s += txt(XR, y + 4, lbl, 10, LIGHT)
        s += f'<rect x="{XR + 72}" y="{y - 3}" width="118" height="5" rx="2.5" fill="{TRACK}"/>\n'
        s += (f'<rect x="{XR + 72}" y="{y - 3}" width="{118 * pct / 100:.0f}" height="5" rx="2.5" '
              f'fill="{GREEN}" style="animation:grow 1.2s ease {.2 + i*.15}s backwards"/>\n')
        s += txt(XR + 198, y + 4, f"{pct:.0f}%", 9, DIMMER)
    s += f'<rect x="{XR}" y="216" width="216" height="30" rx="8" fill="none" stroke="{PILL}"/>\n'
    s += txt(XR + 108, 235, "📄 查看完整日报 →", 11, GREEN, extra=' text-anchor="middle"')
    s += txt(W - 28, H - 16, "POWERED BY github-daily-report", 9, DIMMER, extra=' text-anchor="end"')
    s += "</svg>\n"
    return s


def build_stats(user, contrib, stars):
    W, H = 744, 236
    s = svg_open(W, H, "统计 neofetch")
    s += txt(28, 44, f"~/{USER} $ neofetch --stats", 13, GREEN)
    s += f'<rect x="288" y="34" width="8" height="12" fill="{GREEN}" style="animation:blink 1.1s steps(1) infinite"/>\n'

    rows = [
        ("stars", "?" if stars is None else str(stars), 0.38),
        ("commits", f"{contrib['year_total']}" if contrib["year_total"] is not None else "?", 0.86),
        ("repos", str(user.get("public_repos", "?")), 0.22),
        ("followers", str(user.get("followers", "?")), 0.14),
    ]
    y = 72
    for i, (k, v, frac) in enumerate(rows):
        y += 26
        s += txt(28, y, k, 12, GREEN)
        s += f'<rect x="150" y="{y-10}" width="440" height="8" rx="4" fill="{TRACK}"/>\n'
        s += (f'<rect x="150" y="{y-10}" width="{440*frac:.0f}" height="8" rx="4" fill="{GREEN}" '
              f'style="animation:grow 1.4s cubic-bezier(.2,.8,.2,1) {i*0.15}s backwards"/>\n')
        s += txt(600, y, v, 12, DIM, extra=' text-anchor="end"')
    y += 30
    s += txt(28, y, "languages", 12, GREEN)
    s += txt(150, y, "Python · C · Go · TypeScript", 11, DIM)
    s += "</svg>\n"
    return s


def main():
    os.makedirs(ASSETS, exist_ok=True)
    user = fetch_user()
    events = fetch_events()
    contrib = fetch_contributions()
    rep = fetch_report()
    if not rep:
        rep = {"date": "—", "top": [], "new": 0, "fast": 0, "langs": {}}

    stars = fetch_stars()
    for suffix, pal in PALETTES.items():
        globals().update(pal)
        outs = {
            f"journey{suffix}.svg": build_journey(user, events, contrib),
            f"stats{suffix}.svg": build_stats(user, contrib, stars),
            f"picks{suffix}.svg": build_picks(rep),
        }
        for name, svg in outs.items():
            with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
                f.write(svg)
            print(f"生成 {name}")


if __name__ == "__main__":
    main()
