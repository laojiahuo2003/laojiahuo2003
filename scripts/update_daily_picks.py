#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 github-daily-report 仓库取最新报告，把「新发现项目」Top 5 写进主页 README。
由 .github/workflows/daily-picks.yml 调用，无需本地运行。
"""
import os
import re
import subprocess
import sys

REPORT_REPO = "https://github.com/laojiahuo2003/github-daily-report.git"
README = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "README.md")
START = "<!-- daily-picks:start -->"
END = "<!-- daily-picks:end -->"
TOP_N = 5

def main():
    # 浅克隆报告仓库（只取最新提交，避开 API 限流）
    tmp = "/tmp/daily-report"
    subprocess.run(["rm", "-rf", tmp], check=True)
    subprocess.run(["git", "clone", "--quiet", "--depth", "1", REPORT_REPO, tmp], check=True)

    reports_dir = os.path.join(tmp, "reports")
    files = sorted(f for f in os.listdir(reports_dir) if f.endswith(".md"))
    if not files:
        print("报告目录为空，跳过")
        return
    latest = os.path.join(reports_dir, files[-1])

    with open(latest, encoding="utf-8") as f:
        content = f.read()

    # 报告日期
    m_date = re.match(r"# GitHub 每日报告 - (\S+)", content)
    date_str = m_date.group(1) if m_date else files[-1][:10]

    # 提取「新发现项目」小节条目：- **[name](url)** ⭐123 `Lang`
    section = re.search(r"## ✨ 新发现项目(.*?)(?=\n## |\Z)", content, re.S)
    entries = []
    if section:
        for m in re.finditer(r"- \*\*\[([^\]]+)\]\(([^)]+)\)\*\* ⭐(\d+)(?:[^\n]*?) `(\S+)`", section.group(1)):
            entries.append((m.group(1), m.group(2), int(m.group(3)), m.group(4)))

    lines = [f"**每日精选** · {date_str}", ""]
    if entries:
        for name, url, stars, lang in entries[:TOP_N]:
            stars_h = f"{stars/1000:.1f}k" if stars >= 1000 else str(stars)
            lines.append(f"- [{name}]({url}) · ⭐{stars_h} · `{lang}`")
    else:
        lines.append("*今日报告暂无新发现项目*")
    block = "\n".join(lines)

    with open(README, encoding="utf-8") as f:
        readme = f.read()
    if START not in readme or END not in readme:
        sys.exit("README 中找不到 daily-picks 标记")
    head, rest = readme.split(START, 1)
    _, tail = rest.split(END, 1)
    new_readme = f"{head}{START}\n{block}\n{END}{tail}"

    if new_readme == readme:
        print("内容无变化，跳过提交")
        return
    with open(README, "w", encoding="utf-8") as f:
        f.write(new_readme)
    print(f"已更新每日精选（{date_str}，{min(len(entries), TOP_N)} 项）")

if __name__ == "__main__":
    main()
