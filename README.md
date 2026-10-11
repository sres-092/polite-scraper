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