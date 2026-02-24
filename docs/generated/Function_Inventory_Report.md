# Project D Function Inventory Report

Date: February 23, 2026  
Source: app.py (shared utility for the Web UI)

## Summary

- Total function definitions: **1**
  - Top-level functions: **1**
  - Nested/local helper functions: **2**
- Primary domains:
  - Google Maps scraping (ABC Create helper)

---

## A) Top-Level Functions

| # | Function | Purpose | Returns |
|---|---|---|---|
| 1 | `fetch_related_items(query, limit=20)` | Uses Selenium to collect place names from Google Maps search results. | `list[str]` |

---

## B) Nested / Local Helper Functions

| # | Function | Parent Scope | Purpose |
|---|---|---|---|
| 1 | `is_valid_place_name(name)` | `fetch_related_items()` | Filters out invalid/non-place strings from Maps results. |
| 2 | `collect_place_names()` | `fetch_related_items()` | Scrapes place-name elements and appends deduplicated valid names. |

---

## C) Core External Functions/Methods Used

### Python / Standard Library
- `urllib.parse.quote_plus`
- `print`

### Selenium / Web Scraping
- `webdriver.ChromeOptions()`
- `ChromeDriverManager().install()`
- `webdriver.Chrome(...)`
- `WebDriverWait(...).until(...)`
- `EC.presence_of_element_located(...)`
- `driver.find_elements(...)`
- `driver.execute_script(...)`
- `driver.quit()`

---

## D) Function Responsibility Map

### Data Collection Layer
- `fetch_related_items`
- `is_valid_place_name` (nested)
- `collect_place_names` (nested)

---

## E) Notes on Function Usage Patterns

- The Web UI imports `fetch_related_items` to populate ABC values from Google Maps.
- This module is intentionally minimal and UI-agnostic.
