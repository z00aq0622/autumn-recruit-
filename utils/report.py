"""
日报生成器 - 将爬取结果格式化为Markdown日报
"""
from datetime import datetime
from typing import List, Dict


def generate_daily_report(
    zju_posts: List[Dict],
    boss_jobs: List[Dict],
    niuke_posts: List[Dict],
    guopin_jobs: List[Dict],
    city_posts: List[Dict],
    matched_items: List[Dict]
) -> str:
    """
    生成Markdown格式的秋招日报
    """
    today = datetime.now().strftime("%Y年%m月%d日")
    lines = []

    lines.append(f"# 🐗 秋招日报 | {today}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # === 强烈推荐 ===
    strong_recs = [i for i in matched_items if i.get("match_score", 0) >= 80]
    if strong_recs:
        lines.append("## 🔥 强烈推荐（匹配度 80+）")
        lines.append("")
        for idx, item in enumerate(strong_recs[:10], 1):
            score = item.get("match_score", 0)
            direction = item.get("match_direction", "")
            title = item.get("title", "未知岗位")
            company = item.get("company", "")
            url = item.get("url", "")
            source = item.get("source", "")
            reasons = "、".join(item.get("match_reasons", []))

            lines.append(f"### {idx}. {title}")
            if company:
                lines.append(f"- **公司**: {company}")
            lines.append(f"- **匹配度**: {score}/100 → **{direction}**")
            lines.append(f"- **匹配原因**: {reasons}")
            lines.append(f"- **来源**: {source}")
            if url:
                lines.append(f"- **链接**: [点击查看]({url})")
            lines.append("")

    # === 浙大就业中心 ===
    if zju_posts:
        lines.append("## 🎓 浙大就业中心")
        lines.append("")
        # 按类别分组
        categories = {}
        for post in zju_posts:
            cat = post.get("category", "其他")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(post)

        for cat, items in categories.items():
            lines.append(f"### {cat}")
            lines.append("")
            for item in items[:10]:
                title = item.get("title", "")
                url = item.get("url", "")
                date = item.get("date", "")
                if url:
                    lines.append(f"- [{title}]({url}) {date}")
                else:
                    lines.append(f"- {title} {date}")
            lines.append("")

    # === Boss直聘 ===
    if boss_jobs:
        lines.append("## 💼 Boss直聘校招")
        lines.append("")
        for job in boss_jobs[:15]:
            title = job.get("title", "")
            company = job.get("company", "")
            salary = job.get("salary", "")
            url = job.get("url", "")
            if url:
                lines.append(f"- [{title}]({url}) | {company} | {salary}")
            else:
                lines.append(f"- {title} | {company} | {salary}")
        lines.append("")

    # === 国聘网 ===
    if guopin_jobs:
        lines.append("## 🏛️ 国聘网（央企国企）")
        lines.append("")
        for job in guopin_jobs[:10]:
            title = job.get("title", "")
            company = job.get("company", "")
            url = job.get("url", "")
            if url:
                lines.append(f"- [{title}]({url}) | {company}")
            else:
                lines.append(f"- {title} | {company}")
        lines.append("")

    # === 牛客网 ===
    if niuke_posts:
        lines.append("## 📝 牛客网秋招")
        lines.append("")
        for post in niuke_posts[:10]:
            title = post.get("title", "")
            url = post.get("url", "")
            cat = post.get("category", "")
            if url:
                lines.append(f"- [{title}]({url}) [{cat}]")
            else:
                lines.append(f"- {title} [{cat}]")
        lines.append("")

    # === 城市就业网 ===
    if city_posts:
        lines.append("## 🏙️ 目标城市就业信息")
        lines.append("")
        # 按来源分组
        by_source = {}
        for post in city_posts:
            src = post.get("source", "其他")
            if src not in by_source:
                by_source[src] = []
            by_source[src].append(post)

        for src, items in by_source.items():
            lines.append(f"### {src}")
            lines.append("")
            for item in items[:8]:
                title = item.get("title", "")
                url = item.get("url", "")
                if url:
                    lines.append(f"- [{title}]({url})")
                else:
                    lines.append(f"- {title}")
            lines.append("")

    # === 统计 ===
    lines.append("---")
    lines.append("")
    lines.append("### 📊 今日统计")
    lines.append(f"- 浙大就业: {len(zju_posts)} 条")
    lines.append(f"- Boss直聘: {len(boss_jobs)} 条")
    lines.append(f"- 国聘网: {len(guopin_jobs)} 条")
    lines.append(f"- 牛客网: {len(niuke_posts)} 条")
    lines.append(f"- 城市就业: {len(city_posts)} 条")
    lines.append(f"- **强推岗位: {len(strong_recs)} 个**")
    lines.append("")
    lines.append("> 💡 每日9:00自动推送 | 数据来源: 浙大就业中心 + Boss直聘 + 国聘网 + 牛客网 + 目标城市就业网")
    lines.append("")

    return "\n".join(lines)
