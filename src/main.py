from pathlib import Path
from datetime import datetime, timezone
import json
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


def discover_book_urls() -> dict[str, str]:
    page_url = START_URL
    pages_seen = 0
    discovered = []

    while page_url and pages_seen < MAX_PAGES:
        pages_seen += 1
        html = fetch(page_url, f"catalogue-page-{pages_seen}.html")
        soup = BeautifulSoup(html, "html.parser")

        for link in soup.select("article.product_pod h3 a"):
            discovered.append((urljoin(page_url, link["href"]), page_url))

        next_link = soup.select_one("li.next a")
        page_url = urljoin(page_url, next_link["href"]) if next_link else None

    unique = {}
    for url, source_page in discovered:
        unique.setdefault(url, source_page)

    print(f"catalogue_pages={pages_seen}, discovered={len(discovered)}, unique_urls={len(unique)}")
    return unique


def extract_book(url: str, source_page: str) -> dict:
    slug = url.split("/")[-2]
    cache_name = f"book-{slug}.html"
    html = fetch(url, cache_name)

    fetched_at = datetime.fromtimestamp(
        (CACHE_DIR / cache_name).stat().st_mtime, tz=timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    soup = BeautifulSoup(html, "html.parser")
    product = soup.select_one("div.product_main")

    title = product.select_one("h1")
    price = product.select_one("p.price_color")
    availability = product.select_one("p.availability")
    rating = product.select_one("p.star-rating")
    description = soup.select_one("#product_description + p")

    rating_text = None
    if rating:
        rating_text = next((c for c in rating.get("class", []) if c != "star-rating"), None)

    return {
        "title": title.get_text(strip=True) if title else None,
        "product_url": url,
        "price_text": price.get_text(strip=True) if price else None,
        "availability_text": availability.get_text(strip=True) if availability else None,
        "rating_text": rating_text,
        "description": description.get_text(strip=True) if description else None,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }


def main():
    book_urls = discover_book_urls()
    records = [extract_book(url, source) for url, source in book_urls.items()]
    print(json.dumps(records[0], indent=2, ensure_ascii=False))
    print(f"detail_pages={len(records)}")


if __name__ == "__main__":
    main()