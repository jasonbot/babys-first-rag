import asyncio
import pathlib

from playwright.async_api import Playwright, async_playwright, expect


async def get_transcript_age_links(playwright: Playwright) -> list[str]:
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://www.happyscribe.com/public/the-joe-rogan-experience")
    page_urls = []
    try:
        while True:
            links = await page.evaluate(
                'Array.from(document.getElementsByClassName("hsp-card-episode")).map(a => a.href)'
            )
            page_urls.extend(links)
            async with asyncio.timeout(1):
                await page.get_by_role("link", name="Next ›").click()
    except TimeoutError:
        print("Ran out of pages to click")
    finally:
        await page.close()
        await context.close()
        await browser.close()

    return page_urls

    # ---------------------


async def get_transcript_files(playwright: Playwright, urls: list[str]):
    download_path = pathlib.Path("./transcript_pages")
    download_path.mkdir(exist_ok=True)

    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    for transcript_page_url in urls:
        print(transcript_page_url)
        await page.goto(transcript_page_url)

        filename = f"{transcript_page_url.split("/")[-1]}.html"
        print(filename)
        with open(download_path / filename, "w") as out_handle:
            out_handle.write(await page.content())

async def run(playwright: Playwright) -> list[str]:
    transcript_links = await get_transcript_age_links(playwright)
    await get_transcript_files(playwright, transcript_links)
    


async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)


asyncio.run(main())
