from pathlib import Path
import requests

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/sres-092/polite-scraper)"
TIMEOUT = 10
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

    response = session.get(url, timeout=TIMEOUT)
    if response.status_code != 200:
        raise RuntimeError(f"Fetch failed: {url} returned {response.status_code}")

    response.encoding = "utf-8"
    html = response.text
    cache_path.write_text(html, encoding="utf-8")
    print(f"FETCH      {cache_name}  ({len(html)} chars)")
    return html


def main():
    fetch(START_URL, "catalogue-page-1.html")


if __name__ == "__main__":
    main()
    