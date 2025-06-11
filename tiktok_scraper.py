import asyncio
import os
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

def format_number(number_str):
    number_str = number_str.upper().strip()
    if 'M' in number_str:
        return int(float(number_str.replace('M', '')) * 1_000_000)
    elif 'K' in number_str:
        return int(float(number_str.replace('K', '')) * 1_000)
    return int(number_str.replace(',', ''))

async def scrape_tiktok_profile(username):
    url = f"https://www.tiktok.com/@{username}"
    html_file = "tiktok_page.html"
    result = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(5000)
            html_content = await page.content()

            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            soup = BeautifulSoup(html_content, "html.parser")

            # Get follower/following/likes using data-e2e attributes
            followers_tag = soup.find("strong", {"data-e2e": "followers-count"})
            following_tag = soup.find("strong", {"data-e2e": "following-count"})
            likes_tag = soup.find("strong", {"data-e2e": "likes-count"})
            bio_tag = soup.find("h2", {"data-e2e": "user-bio"})
            link_tag = soup.find("a", {"data-e2e": "user-link"})

            if followers_tag and following_tag and likes_tag:
                result["followers"] = format_number(followers_tag.text)
                result["following"] = format_number(following_tag.text)
                result["likes"] = format_number(likes_tag.text)
                result["bio"] = bio_tag.get_text(separator=" ", strip=True) if bio_tag else ""
                result["link"] = link_tag["href"] if link_tag and link_tag.has_attr("href") else ""
                result["name"] = soup.title.string.replace(" on TikTok", "").strip() if soup.title else ""
        finally:
            await browser.close()

    # Remove file if data was successfully extracted
    if result.get("followers"):
        try:
            os.remove(html_file)
        except Exception:
            pass

    return result

if __name__ == "__main__":
    username = input("Enter TikTok username (without @): ").strip()
    data = asyncio.run(scrape_profile_data(username))
    if data:
        print(json.dumps(data, indent=2))
    else:
        print("No profile data found. Check tiktok_page.html for debugging.")
