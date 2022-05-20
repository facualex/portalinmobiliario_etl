from scraper import Scraper
import asyncio

async def main():
    scraper = Scraper()
    await scraper.start_scrape(write_results_to_json=False)

if __name__ == "__main__":
    asyncio.run(main())
