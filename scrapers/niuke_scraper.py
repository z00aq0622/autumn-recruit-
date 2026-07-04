"""
牛客网秋招爬虫 - 获取最新秋招讨论和岗位信息
"""
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from dataclasses import dataclass
from typing import List


@dataclass
class NiukePost:
    title: str
    author: str
    url: str
    source: str = "牛客网"
    category: str = ""  # 求职/面经/内推


async def scrape_niuke_campus() -> List[NiukePost]:
    """爬取牛客网秋招专区"""
    posts = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()

        # 秋招讨论区
        try:
            url = "https://www.nowcoder.com/discuss/tag/644"
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            items = await page.query_selector_all(".discuss-main, .list-item, .nc-post-item")
            for item in items[:30]:
                try:
                    a_tag = await item.query_selector("a")
                    if not a_tag:
                        continue
                    title = (await a_tag.inner_text()).strip()
                    href = await a_tag.get_attribute("href")
                    if not title or len(title) < 4:
                        continue
                    if href and not href.startswith("http"):
                        href = "https://www.nowcoder.com" + href

                    posts.append(NiukePost(
                        title=title[:80],
                        author="",
                        url=href or "",
                        category="秋招讨论"
                    ))
                except Exception:
                    continue
        except Exception as e:
            print(f"[牛客-秋招讨论] 爬取失败: {e}")

        # 校招内推区
        try:
            url = "https://www.nowcoder.com/discuss/tag/714"
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            items = await page.query_selector_all(".discuss-main, .list-item, .nc-post-item")
            for item in items[:20]:
                try:
                    a_tag = await item.query_selector("a")
                    if not a_tag:
                        continue
                    title = (await a_tag.inner_text()).strip()
                    href = await a_tag.get_attribute("href")
                    if not title or len(title) < 4:
                        continue
                    if href and not href.startswith("http"):
                        href = "https://www.nowcoder.com" + href

                    posts.append(NiukePost(
                        title=title[:80],
                        author="",
                        url=href or "",
                        category="校招内推"
                    ))
                except Exception:
                    continue
        except Exception as e:
            print(f"[牛客-校招内推] 爬取失败: {e}")

        await browser.close()

    return posts


if __name__ == "__main__":
    asyncio.run(main())
    print("牛客网爬虫模块加载完成")
