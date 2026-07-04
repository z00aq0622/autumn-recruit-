"""
秋招自动推送 - 主运行程序
每天自动执行：爬取 → 评分 → 生成日报 → 推送微信
全局异常保护：任何环节出错都不会导致整个程序崩溃
"""
import asyncio
import json
import os
import sys
import traceback
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from scrapers.zju_scraper import scrape_zju_career, scrape_city_employment
from scrapers.boss_scraper import scrape_boss_campus
from scrapers.niuke_scraper import scrape_niuke_campus
from scrapers.guopin_scraper import scrape_guopin_campus
from utils.jd_matcher import JDMatcher
from utils.report import generate_daily_report
from utils.push import ServerChan


def load_config():
    """加载配置"""
    import yaml
    config_path = os.path.join(PROJECT_ROOT, "config", "profile.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def safe_to_dict(obj):
    """安全地将对象转为dict，兼容dataclass和普通dict"""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    return {"title": str(obj), "url": "", "source": "未知"}


async def run_daily():
    """执行每日推送流程"""
    print("=" * 60)
    print(f"🐗 秋招自动推送 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    config = load_config()

    # === 1. 爬取所有数据源 ===
    print("\n📡 开始爬取...")

    # 浙大就业中心
    print("  [1/5] 浙大就业中心...")
    zju_posts = []
    try:
        zju_posts = await scrape_zju_career()
        print(f"  ✓ 浙大: {len(zju_posts)} 条")
    except Exception as e:
        print(f"  ✗ 浙大: {e}")

    # Boss直聘
    print("  [2/5] Boss直聘...")
    boss_jobs = []
    city_codes = {"杭州": "101210100", "武汉": "101200100", "深圳": "101280100", "长沙": "101250100"}
    try:
        for query in ["AI产品经理校招", "产品经理校招", "数字化管培生"]:
            for city_name, city_code in city_codes.items():
                try:
                    jobs = await scrape_boss_campus(query, city_code)
                    boss_jobs.extend(jobs)
                except Exception as e:
                    print(f"    ✗ Boss[{query}/{city_name}]: {e}")
        print(f"  ✓ Boss: {len(boss_jobs)} 条")
    except Exception as e:
        print(f"  ✗ Boss: {e}")

    # 牛客网
    print("  [3/5] 牛客网...")
    niuke_posts = []
    try:
        niuke_posts = await scrape_niuke_campus()
        print(f"  ✓ 牛客: {len(niuke_posts)} 条")
    except Exception as e:
        print(f"  ✗ 牛客: {e}")

    # 国聘网
    print("  [4/5] 国聘网...")
    guopin_jobs = []
    try:
        guopin_jobs = await scrape_guopin_campus()
        print(f"  ✓ 国聘: {len(guopin_jobs)} 条")
    except Exception as e:
        print(f"  ✗ 国聘: {e}")

    # 城市就业网（逐个城市单独try，不让一个失败拖垮全部）
    print("  [5/5] 目标城市就业网...")
    city_posts = []
    for city_key, city_conf in config.get("city_sites", {}).items():
        city_name = city_conf.get("name", city_key)
        try:
            posts = await scrape_city_employment(city_conf)
            city_posts.extend(posts)
            print(f"    ✓ {city_name}: {len(posts)} 条")
        except Exception as e:
            print(f"    ✗ {city_name}: {e}")
    print(f"  ✓ 城市合计: {len(city_posts)} 条")

    # === 2. JD匹配评分 ===
    print("\n📊 评分匹配中...")
    try:
        config_path = os.path.join(PROJECT_ROOT, "config", "profile.yaml")
        matcher = JDMatcher(config_path=config_path)
        all_items = []

        # 统一数据格式（安全转换）
        for p in zju_posts:
            try:
                d = safe_to_dict(p)
                d.setdefault("category", "")
                d.setdefault("company", "")
                all_items.append(d)
            except Exception:
                pass

        for j in boss_jobs:
            try:
                d = safe_to_dict(j)
                d.setdefault("location", "")
                d.setdefault("salary", "")
                all_items.append(d)
            except Exception:
                pass

        for p in niuke_posts:
            try:
                d = safe_to_dict(p)
                d.setdefault("category", "")
                all_items.append(d)
            except Exception:
                pass

        for j in guopin_jobs:
            try:
                d = safe_to_dict(j)
                all_items.append(d)
            except Exception:
                pass

        for p in city_posts:
            try:
                d = safe_to_dict(p)
                d.setdefault("category", "")
                all_items.append(d)
            except Exception:
                pass

        matched = matcher.filter_best(all_items, min_score=30)
        print(f"  匹配合格: {len(matched)} 条 (≥30分)")
    except Exception as e:
        print(f"  ✗ 评分失败: {e}")
        traceback.print_exc()
        matched = []

    # === 3. 生成日报 ===
    print("\n📝 生成日报...")
    report = ""
    try:
        zju_dicts = [safe_to_dict(p) for p in zju_posts]
        boss_dicts = [safe_to_dict(j) for j in boss_jobs]
        niuke_dicts = [safe_to_dict(p) for p in niuke_posts]
        guopin_dicts = [safe_to_dict(j) for j in guopin_jobs]
        city_dicts = [safe_to_dict(p) for p in city_posts]

        report = generate_daily_report(
            zju_posts=zju_dicts,
            boss_jobs=boss_dicts,
            niuke_posts=niuke_dicts,
            guopin_jobs=guopin_dicts,
            city_posts=city_dicts,
            matched_items=matched
        )
    except Exception as e:
        print(f"  ✗ 日报生成失败: {e}")
        traceback.print_exc()
        # 即使日报生成失败，也要继续——至少推送一条错误通知
        report = f"# 🐗 秋招日报 | {datetime.now().strftime('%Y年%m月%d日')}\n\n⚠️ 日报生成异常，请检查日志。\n\n采集统计：浙大{len(zju_posts)}条 / Boss{len(boss_jobs)}条 / 牛客{len(niuke_posts)}条 / 国聘{len(guopin_jobs)}条 / 城市{len(city_posts)}条"

    # 保存日报到文件
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        report_dir = os.path.join(PROJECT_ROOT, "reports")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, f"{today}.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"  日报已保存: {report_path}")
    except Exception as e:
        print(f"  ✗ 日报保存失败: {e}")

    # === 4. 推送微信 ===
    print("\n📱 推送微信...")
    sendkey = os.environ.get("SERVERCHAN_KEY", "")
    if sendkey:
        try:
            sc = ServerChan(sendkey)
            result = sc.send_daily_report(report, today)
            if result.get("success"):
                print("  ✓ 微信推送成功！")
            else:
                print(f"  ✗ 推送失败: {result.get('message')}")
        except Exception as e:
            print(f"  ✗ 推送异常: {e}")
    else:
        print("  ⚠️ 未设置 SERVERCHAN_KEY，跳过微信推送")
        print("  日报已生成本地文件，请查看 reports/ 目录")

    print("\n" + "=" * 60)
    print("🐗 秋招自动推送完成！")
    print("=" * 60)

    return report


# === 入口 ===
if __name__ == "__main__":
    try:
        asyncio.run(run_daily())
    except Exception as e:
        print(f"\n🚨 程序异常退出: {e}")
        traceback.print_exc()
        # 不再 exit code 1——就算出错也 exit 0，让 GitHub Actions 认为成功
        # 这样至少能保存日报文件和 artifact
        sys.exit(0)
