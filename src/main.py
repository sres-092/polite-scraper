from pathlib import Path
from datetime import datetime, timezone
import json
import re
import requests
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, ValidationError, field_validator

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/sres-092/polite-scraper)"
TIMEOUT = 10
DELAY_SECONDS = 0.5
MAX_PAGES = 3
CACHE_DIR = Path("cache")
OUTPUT_DIR = Path("output")
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})


class Book(BaseModel):
    title: str = Field(min_length=1)
    product_url: str
    price_text: str
    price_gbp: float = Field(gt=0)
    availability_text: str
    available_count: int | None
    rating_text: str
    rating: int = Field(ge=1, le=5)
    description: str | None
    source_page: str
    fetched_at: str

    @field_validator("product_url", "source_page")
    @classmethod
    def must_be_https(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("URL must start with https://")
        return value


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


def normalize(raw: dict) -> dict:
    record = dict(raw)

    price_match = re.search(r"\d+(\.\d+)?", raw.get("price_text") or "")
    record["price_gbp"] = float(price_match.group()) if price_match else None

    count_match = re.search(r"\((\d+) available\)", raw.get("availability_text") or "")
    record["available_count"] = int(count_match.group(1)) if count_match else None

    record["rating"] = RATING_WORDS.get(raw.get("rating_text"))
    return record


def validate_and_store(raw_records: list[dict]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    valid = {}
    errors = []

    for raw in raw_records:
        record = normalize(raw)
        try:
            book = Book(**record)
        except ValidationError as error:
            errors.append({"product_url": raw.get("product_url"), "reason": str(error)})
            continue
        valid[book.product_url] = book.model_dump()

    with open(OUTPUT_DIR / "books.json", "w", encoding="utf-8") as f:
        json.dump(list(valid.values()), f, indent=2, ensure_ascii=False)
    with open(OUTPUT_DIR / "errors.json", "w", encoding="utf-8") as f:
        json.dump(errors, f, indent=2, ensure_ascii=False)

    print(f"valid_records={len(valid)}, invalid_records={len(errors)}")


def main():
    book_urls = discover_book_urls()
    raw_records = [extract_book(url, source) for url, source in book_urls.items()]
    print(f"detail_pages={len(raw_records)}")
    validate_and_store(raw_records)


if __name__ == "__main__":
    main()