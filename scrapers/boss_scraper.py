"""
Boss直聘 爬虫 - 聚焦秋招校招岗位
使用Playwright模拟浏览器搜索
"""
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from dataclasses import dataclass
from typing import List


@dataclass
class BossJob:
    title: str
    company: str
    salary: str
    location: str
    url: str
    tags: str = ""
    source: str = "Boss直聘"


async def scrape_boss_campus(query: str = "产品经理校招", city: str = "101210100") -> List[BossJob]:
    """
    爬取Boss直聘校招岗位
    city code: 101210100=杭州, 101200100=武汉, 101250100=长沙, 101280100=深圳, 101020100=上海
    """
    jobs = []
    base_url = "https://www.zhipin.com"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1440, "height": 900}
        )
        page = await context.new_page()

        try:
            # Boss直聘校招搜索
            search_url = f"{base_url}/web/geek/job?query={query}&city={city}&experience=校招"
            await page.goto(search_url, timeout=20000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            # 等待岗位列表加载
            job_cards = await page.query_selector_all(".job-card-wrapper, .job-card-left, .search-job-result li")
            for card in job_cards[:20]:
                try:
                    title_el = await card.query_selector(".job-name, .job-title, h3")
                    company_el = await card.query_selector(".company-name, .name")
                    salary_el = await card.query_selector(".salary, .red")
                    location_el = await card.query_selector(".job-area, .job-detail")
                    link_el = await card.query_selector("a")

                    title = (await title_el.inner_text()).strip() if title_el else ""
                    company = (await company_el.inner_text()).strip() if company_el else ""
                    salary = (await salary_el.inner_text()).strip() if salary_el else ""
                    location = (await location_el.inner_text()).strip() if location_el else ""
                    href = await link_el.get_attribute("href") if link_el else ""

                    if title:
                        if href and not href.startswith("http"):
                            href = base_url + href
                        jobs.append(BossJob(
                            title=title,
                            company=company,
                            salary=salary,
                            location=location,
                            url=href or ""
                        ))
                except Exception:
                    continue

        except Exception as e:
            print(f"[Boss直聘] 爬取失败: {e}")

        await browser.close()

    return jobs


# === 测试入口 ===
async def main():
    print("Boss直聘爬虫测试...")
    jobs = await scrape_boss_campus("AI产品经理", "101210100")
    print(f"获取到 {len(jobs)} 个岗位")
    for j in jobs[:5]:
        print(f"  {j.company} - {j.title} | {j.salary}")


if __name__ == "__main__":
    asyncio.run(main())
