"""
浙大就业中心爬虫
爬取校招公告、宣讲会、专场招聘信息
"""
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from dataclasses import dataclass, asdict
from typing import List


@dataclass
class JobPost:
    """招聘岗位数据结构"""
    title: str
    url: str
    company: str = ""
    date: str = ""
    source: str = ""
    location: str = ""
    category: str = ""  # 校招/宣讲会/专场/人才引进


async def scrape_zju_career(max_pages: int = 3) -> List[JobPost]:
    """爬取浙大就业中心最新招聘信息"""
    posts = []
    base_url = "https://www.career.zju.edu.cn"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()

        # === 1. 校招公告 ===
        try:
            url = f"{base_url}/jyxt/jygz/new.htm"
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            items = await page.query_selector_all("li.clearfix, div.list-item, tr, .news-list li")
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
                        href = base_url + href

                    date_text = ""
                    date_el = await item.query_selector(".date, .time, span")
                    if date_el:
                        date_text = (await date_el.inner_text()).strip()

                    posts.append(JobPost(
                        title=title,
                        url=href or "",
                        company="",
                        date=date_text,
                        source="浙大就业中心",
                        category="校招公告"
                    ))
                except Exception:
                    continue
        except Exception as e:
            print(f"[浙大-校招公告] 爬取失败: {e}")

        # === 2. 宣讲会 ===
        try:
            url = f"{base_url}/jyxt/xjh/new.htm"
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            items = await page.query_selector_all("li.clearfix, div.list-item, tr, .news-list li")
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
                        href = base_url + href

                    posts.append(JobPost(
                        title=title,
                        url=href or "",
                        source="浙大就业中心",
                        category="宣讲会"
                    ))
                except Exception:
                    continue
        except Exception as e:
            print(f"[浙大-宣讲会] 爬取失败: {e}")

        await browser.close()

    return posts


async def scrape_city_employment(city_config: dict) -> List[JobPost]:
    """爬取城市就业网站信息"""
    posts = []
    city_name = city_config.get("name", "")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()

        for site in city_config.get("urls", []):
            site_name = site["name"]
            url = site["url"]
            try:
                await page.goto(url, timeout=15000, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)

                # 通用策略：找所有链接，筛选含关键词的
                keywords = ["招聘", "招录", "公告", "选调", "人才", "事业编", "校招", "考试"]
                all_links = await page.query_selector_all("a")

                for link in all_links[:100]:
                    try:
                        text = (await link.inner_text()).strip()
                        href = await link.get_attribute("href")
                        if not text or len(text) < 6:
                            continue
                        # 只保留含招聘相关关键词的
                        if not any(kw in text for kw in keywords):
                            continue
                        if href and not href.startswith("http"):
                            if href.startswith("/"):
                                href = url.rstrip("/") + href
                            else:
                                href = url + "/" + href

                        posts.append(JobPost(
                            title=text[:80],
                            url=href or "",
                            source=f"{city_name}-{site_name}",
                            category="城市就业"
                        ))
                    except Exception:
                        continue

                # 去重
                seen = set()
                unique = []
                for post in posts:
                    if post.title not in seen:
                        seen.add(post.title)
                        unique.append(post)
                posts = unique

            except Exception as e:
                print(f"[{city_name}-{site_name}] 爬取失败: {e}")

        await browser.close()

    return posts


# === 测试入口 ===
async def main():
    print("=" * 50)
    print("浙大就业中心爬虫测试")
    print("=" * 50)

    zju_posts = await scrape_zju_career()
    print(f"\n浙大就业中心: 获取到 {len(zju_posts)} 条信息")
    for p in zju_posts[:5]:
        print(f"  [{p.category}] {p.title}")

    print("\n测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
