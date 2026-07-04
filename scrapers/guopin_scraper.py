"""
国聘网爬虫 - 央企国企校招信息
"""
import asyncio
from playwright.async_api import async_playwright
from dataclasses import dataclass
from typing import List


@dataclass
class GuoPinJob:
    title: str
    company: str
    url: str
    date: str = ""
    source: str = "国聘网"


async def scrape_guopin_campus() -> List[GuoPinJob]:
    """爬取国聘网校招岗位"""
    jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            url = "https://www.iguopin.com/job/list?category=1"
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            items = await page.query_selector_all(".job-item, .list-item, .job-card")
            for item in items[:30]:
                try:
                    title_el = await item.query_selector(".job-name, .title, h3")
                    company_el = await item.query_selector(".company-name, .company, .name")
                    link_el = await item.query_selector("a")

                    title = (await title_el.inner_text()).strip() if title_el else ""
                    company = (await company_el.inner_text()).strip() if company_el else ""
                    href = await link_el.get_attribute("href") if link_el else ""

                    if title:
                        if href and not href.startswith("http"):
                            href = "https://www.iguopin.com" + href
                        jobs.append(GuoPinJob(
                            title=title[:80],
                            company=company,
                            url=href or ""
                        ))
                except Exception:
                    continue

        except Exception as e:
            print(f"[国聘网] 爬取失败: {e}")

        await browser.close()

    return jobs


if __name__ == "__main__":
    asyncio.run(main())
