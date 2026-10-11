from pathlib import Path
import requests
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/sres-092/polite-scraper)"
TIMEOUT = 10
DELAY_SECONDS = 0.5
MAX_PAGES = 3
CACHE_DIR = Path("cache")
START_URL = "https://books.toscrape.com/catalogue/page-1.html"

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})


def fetch(url: str, cache_name: str) -> str:
    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = CACHE_DIR / cache_name

    if cache_path.exists():
        html = cache_path.read_text(encoding="utf-8")
        print(f"CACHE HIT  {cache_name}  ({len(html)} chars)")
        return html

    time.sleep(DELAY_SECONDS)
    response = session.get(url, timeout=TIMEOUT)
    if response.status_code != 200:
        raise RuntimeError(f"Fetch failed: {url} returned {response.status_code}")

    response.encoding = "utf-8"
    html = response.text
    cache_path.write_text(html, encoding="utf-8")
    print(f"FETCH      {cache_name}  ({len(html)} chars)")
    return html


def discover_book_urls() -> list[str]:
    page_url = START_URL
    pages_seen = 0
    discovered = []

    while page_url and pages_seen < MAX_PAGES:
        pages_seen += 1
        html = fetch(page_url, f"catalogue-page-{pages_seen}.html")
        soup = BeautifulSoup(html, "html.parser")

        for link in soup.select("article.product_pod h3 a"):
            discovered.append(urljoin(page_url, link["href"]))

        next_link = soup.select_one("li.next a")
        page_url = urljoin(page_url, next_link["href"]) if next_link else None

    unique_urls = list(dict.fromkeys(discovered))
    print(f"catalogue_pages={pages_seen}, discovered={len(discovered)}, unique_urls={len(unique_urls)}")
    return unique_urls


def main():
    discover_book_urls()


if __name__ == "__main__":
    main()