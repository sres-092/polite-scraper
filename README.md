# Polite Scraper

A small, polite scraper that collects 60 books from Books to Scrape and turns
messy HTML into clean, schema-checked JSON.

## Target classification

- **Site:** https://books.toscrape.com
- **Why it's allowed:** toscrape.com describes itself as a "Web Scraping
  Sandbox" — "a safe place for beginners learning web scraping and for
  developers validating their scraping technologies." Books to Scrape is
  described as "a fictional bookstore that desperately wants to be scraped."
- **Scope:** the first 3 catalogue pages only — 60 books
- **Data collected:** title, price, availability, star rating, description,
  and product URL. No personal data.
- **robots.txt:** requested https://books.toscrape.com/robots.txt once — no
  robots file found (404). A missing file is not permission; the sandbox
  statement above is.
- **Why this is appropriate:** the site exists specifically so people can
  practise scraping, and the scope is small and fixed.

I will not reuse this code on another site without checking its rules and terms first.

## How to run it

Python lane: `requests` for fetching, `Beautiful Soup` for parsing, `Pydantic`
for validation.

```
git clone https://github.com/sres-092/polite-scraper.git
cd polite-scraper
python -m venv venv
venv\Scripts\Activate.ps1        # Windows
source venv/bin/activate         # Mac/Linux
pip install -r requirements.txt
python src/main.py
```

The run writes three files to `output/`: `books.json` (valid records),
`errors.json` (records that failed validation, with the reason), and
`run-report.json` (what happened during the run).

## Record schema

Every record in `books.json` has been checked against this Pydantic schema
before being stored:

| Field | Type | Notes |
|-------|------|-------|
| title | string | required, not empty |
| product_url | string | canonical identity, must start with `https://` |
| price_text | string | raw value as on the page, e.g. `"£51.77"` |
| price_gbp | number | normalized, must be greater than 0 |
| availability_text | string | raw value, e.g. `"In stock (22 available)"` |
| available_count | integer or null | number pulled from availability text |
| rating_text | string | raw value, e.g. `"Three"` |
| rating | integer | 1 to 5 |
| description | string or null | `null` when the page has none — never invented |
| source_page | string | catalogue page the book was found on |
| fetched_at | string | when the page was actually fetched (UTC) |

## Politeness rules

- **User-agent:** every request identifies itself as
  `FlyRankInternship-A9/1.0 (+https://github.com/sres-092/polite-scraper)`
- **Delay:** at least 0.5 seconds between real requests to the site
- **Timeout:** every request gives up after 10 seconds
- **Cache:** every page is saved to `cache/` on first fetch and read from disk
  afterwards, so the site is contacted once per page, not once per run
- **Retries:** a timeout or `5xx` is retried once after a short wait. A `404`
  or `403` is never retried.

## Sample run report

A real `run-report.json` from a cached run, with one deliberately broken URL
included to prove a failure doesn't stop the run:

```json
{
  "started_at": "2026-10-11T23:45:58Z",
  "duration_seconds": 2.32,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1,
  "failures": [
    {
      "url": "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html",
      "reason": "status 404"
    }
  ]
}
```

## Why no browser

The book data is already in the HTML the server sends, so a plain HTTP request
gets everything. A headless browser would only add cost and slowness.

## Honest limitation

The selectors are written for this site's exact HTML. If Books to Scrape
changed its page structure, extraction would break and records would land in
`errors.json` rather than `books.json` — which is the point of validating, but
the selectors would still need updating by hand. Descriptions are also stored
exactly as the site provides them, including its own repeated text and
"...more" endings.

## Ethics

Be honest about who you are and use an official API whenever one exists. Never
try to cheat or bypass logins, paywalls or blocks. Gather and keep only what you
need — nothing in excess, and nothing that could be used maliciously.