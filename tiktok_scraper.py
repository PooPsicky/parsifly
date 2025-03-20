import asyncio
import os
import openai
import pandas as pd
from playwright.async_api import async_playwright

# Load OpenAI API Key from environment variables or Streamlit Cloud Secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


async def generate_summary(caption):
    """Generate a short summary of a TikTok video using GPT-3.5 Turbo."""

    if not caption or caption == "No Caption":
        return "No meaningful caption available."

    try:
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a TikTok content analyst. Summarize this TikTok video briefly."},
                {"role": "user", "content": caption}
            ],
            max_tokens=50,
            temperature=0.6
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "Summary unavailable."


async def scrape_tiktok_profile(username, num_videos=10):
    """Scrape a TikTok profile's latest videos using Playwright in headless mode."""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/home/adminuser/.cache/ms-playwright/chrome-linux64/chrome",
            headless=True
        )
        page = await browser.new_page()

        # Open TikTok profile
        url = f"https://www.tiktok.com/@{username}"
        await page.goto(url)
        await page.wait_for_timeout(5000)  # Wait for the page to load

        videos = []
        video_elements = await page.query_selector_all('div[data-e2e="user-post-item"]')

        for video in video_elements[:num_videos]:
            try:
                video_link = await video.query_selector("a")
                video_url = await video_link.get_attribute("href") if video_link else "N/A"

                caption_element = await video.query_selector("img")
                caption = await caption_element.get_attribute("alt") if caption_element else "No Caption"

                views_element = await video.query_selector('strong[data-e2e="video-views"]')
                views = await views_element.inner_text() if views_element else "0"

                likes_element = await video.query_selector('span[data-e2e="like-count"]')
                likes = await likes_element.inner_text() if likes_element else "0"

                comments_element = await video.query_selector('span[data-e2e="comment-count"]')
                comments = await comments_element.inner_text() if comments_element else "0"

                shares_element = await video.query_selector('span[data-e2e="share-count"]')
                shares = await shares_element.inner_text() if shares_element else "0"

                summary = await generate_summary(caption)  # Generate summary using GPT-3.5 Turbo

                videos.append({
                    "Video Link": video_url,
                    "Caption": caption,
                    "Views": views,
                    "Likes": likes,
                    "Comments": comments,
                    "Shares": shares,
                    "Summary": summary
                })
            except Exception as e:
                print(f"Error scraping video: {e}")

        await browser.close()

        return pd.DataFrame(videos)


# Run scraper if executed directly
if __name__ == "__main__":
    username = "garyseconomics"  # Example username
    num_videos = 10
    df = asyncio.run(scrape_tiktok_profile(username, num_videos))
    print(df)
