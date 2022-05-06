from scraper import Scraper
import json
import asyncio

async def main():
    scraper = Scraper()
    await scraper.start_scrape()

if __name__ == "__main__":
    asyncio.run(main())
