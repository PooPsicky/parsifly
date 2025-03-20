import asyncio
import sys
import json
import os
from playwright.async_api import async_playwright
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

async def generate_summary(caption):
    prompt = f"""
    You're an expert social media analyst.
    Given the following TikTok caption, write a concise and engaging summary highlighting:
    - Main topic or product being promoted
    - Emotional tone (exciting, funny, informative, etc.)
    - What might attract viewers to watch this video

    Caption:
    "{caption}"

    Engaging Summary:
    """
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=60,
        temperature=0.7  # Clearly improves creativity
    )
    return response.choices[0].message.content.strip()


async def scrape_tiktok_profile(profile_url, num_videos):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/home/adminuser/.cache/ms-playwright/chrome-linux64/chrome",
            headless=True
        )
        page = await browser.new_page()
        await page.goto(profile_url)

        videos_loaded = 0
        while videos_loaded < num_videos:
            await page.mouse.wheel(0, 1500)
            await asyncio.sleep(2)
            videos_loaded = len(await page.query_selector_all('div[data-e2e="user-post-item"]'))

        video_elements = (await page.query_selector_all('div[data-e2e="user-post-item"]'))[:num_videos]

        video_data = []
        for video in video_elements:
            video_link_el = await video.query_selector('a')
            caption_el = await video.query_selector('img')
            views_el = await video.query_selector('strong[data-e2e="video-views"]')

            video_link = await video_link_el.get_attribute('href')
            caption = await caption_el.get_attribute('alt')
            views = await views_el.inner_text() if views_el else "N/A"

            video_full_link = video_link if video_link.startswith('http') else f"https://www.tiktok.com{video_link}"

            detail_page = await browser.new_page()
            await detail_page.goto(video_full_link)
            await detail_page.wait_for_selector('strong[data-e2e="like-count"]', timeout=10000)

            try:
                likes_el = await detail_page.query_selector('strong[data-e2e="like-count"]')
                likes = await likes_el.inner_text() if likes_el else 'N/A'
            except:
                likes = 'N/A'

            try:
                comments_el = await detail_page.query_selector('strong[data-e2e="comment-count"]')
                comments = await comments_el.inner_text() if comments_el else 'N/A'
            except:
                comments = 'N/A'

            try:
                shares_el = await detail_page.query_selector('strong[data-e2e="share-count"]')
                shares = await shares_el.inner_text() if shares_el else 'N/A'
            except:
                shares = 'N/A'

            await detail_page.close()

            summary = await generate_summary(caption)

            video_data.append({
                "video_link": video_full_link,
                "caption": caption,
                "content_summary": summary,
                "views": views,
                "likes": likes,
                "comments": comments,
                "shares": shares,
            })

        await browser.close()

        with open("tiktok_results.json", "w", encoding="utf-8") as f:
            json.dump(video_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    profile_url = sys.argv[1]
    num_videos_to_scrape = int(sys.argv[2])
    asyncio.run(scrape_tiktok_profile(profile_url, num_videos_to_scrape))
