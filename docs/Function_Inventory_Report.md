# Project D Function Inventory Report

Date: February 23, 2026  
Source: `app.py`

## Summary

- Total function definitions: **20**
  - Top-level functions: **16**
  - Nested/local helper functions: **4**
- Primary domains:
  - CLI display/input formatting
  - Google Sheets worksheet resolution and persistence
  - Google Maps scraping
  - LangGraph node pipeline
  - Quiz flow and quiz-results logging

---

## A) Top-Level Functions

| # | Function | Purpose | Returns |
|---|---|---|---|
| 1 | `_center_print(text="", indent=0)` | Centers terminal output while handling ANSI color code width correctly. | `None` |
| 2 | `_center_input(prompt="")` | Centers input prompts while handling ANSI color code width correctly. | `str` |
| 3 | `_get_quiz_results_worksheet(spreadsheet)` | Gets or creates the `Quiz Results` worksheet and initializes headers if needed. | Worksheet object |
| 4 | `_save_quiz_result(spreadsheet, worksheet_name, status="Completed")` | Appends a quiz completion row (timestamp, worksheet, status). | `None` |
| 5 | `_display_quiz_results(spreadsheet)` | Reads and displays quiz result history, newest first. | `None` |
| 6 | `_next_worksheet_name(spreadsheet, base_name)` | Builds a unique worksheet name using timestamp/suffix when needed. | `str` |
| 7 | `_open_target_worksheet(spreadsheet, base_name, allow_overwrite)` | Opens/creates target worksheet with overwrite safety prompts. | `(worksheet, worksheet_name)` or `(None, None)` |
| 8 | `_resolve_spreadsheet_title(cfg)` | Resolves spreadsheet title from ID and caches it in config. | `str | None` |
| 9 | `fetch_related_items(query, limit=20)` | Uses Selenium to collect place names from Google Maps search results. | `list[str]` |
| 10 | `set_abc(state)` | LangGraph node that merges `to_set` into `abc`. | `dict` |
| 11 | `show_abc(state)` | LangGraph node that passes state through for display stage. | `dict` |
| 12 | `interactive_set(state)` | Placeholder node (no-op) for interactive behavior handled in `main()`. | `dict` |
| 13 | `gs_load_node(state)` | LangGraph node that loads worksheet key/value pairs into `abc`. | `dict` |
| 14 | `gs_save_node(state)` | LangGraph node that writes `abc` back to Google Sheets worksheet. | `dict` |
| 15 | `build_graph()` | Creates graph nodes and edges (`START -> gs_load -> set_abc -> gs_save -> show_abc`). | `StateGraph` |
| 16 | `main()` | Runs CLI app, menu system, worksheet ops, ABC ops, quiz, and quiz results view. | `None` |

---

## B) Nested / Local Helper Functions

| # | Function | Parent Scope | Purpose |
|---|---|---|---|
| 1 | `is_valid_place_name(name)` | `fetch_related_items()` | Filters out invalid/non-place strings from Maps results. |
| 2 | `collect_place_names()` | `fetch_related_items()` | Scrapes place-name elements and appends deduplicated valid names. |
| 3 | `_print_fixed_keys_values(d, fixed_keys, cols=4)` | `main()` | Prints A–Z grouped values with centered colored output. |
| 4 | `_print_quiz_graph_for_review()` | Choice 9 block in `main()` | Shows current populated quiz key/value set for review after repeated mistakes. |

---

## C) Core External Functions/Methods Used

### Python / Standard Library
- `argparse.ArgumentParser`, `parse_args`
- `datetime.now().strftime`
- `os.getenv`
- `random.choice`
- `shutil.get_terminal_size`
- `urllib.parse.quote_plus`
- `input`, `print`

### LangGraph
- `StateGraph(...)`
- `graph.add_node(...)`
- `graph.add_edge(...)`
- `graph.compile()`
- `compiled.invoke(...)`

### Google Sheets (`gspread` + Google Auth)
- `Credentials.from_service_account_file(...)`
- `gspread.authorize(...)`
- `client.open_by_key(...)`
- `spreadsheet.worksheet(...)`
- `spreadsheet.worksheets()`
- `spreadsheet.add_worksheet(...)`
- `worksheet.get_all_values()`
- `worksheet.update(...)`
- `worksheet.append_row(...)`
- `worksheet.clear()`
- `worksheet.resize(...)`

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

### UI/Formatting Layer
- `_center_print`
- `_center_input`
- `_display_quiz_results` (presentation-focused)
- `_print_fixed_keys_values` (nested)

### Worksheet & Persistence Layer
- `_next_worksheet_name`
- `_open_target_worksheet`
- `_resolve_spreadsheet_title`
- `_get_quiz_results_worksheet`
- `_save_quiz_result`
- `gs_load_node`
- `gs_save_node`

### Data Collection Layer
- `fetch_related_items`
- `is_valid_place_name` (nested)
- `collect_place_names` (nested)

### Graph / App Orchestration Layer
- `set_abc`
- `show_abc`
- `interactive_set`
- `build_graph`
- `main`
- `_print_quiz_graph_for_review` (nested in quiz branch)

---

## E) Notes on Function Usage Patterns

- The application uses **menu-driven orchestration** in `main()` with heavy branch-based flow control.
- Google Sheets access is intentionally repeated in branches to keep each menu action self-contained.
- Quiz result logging is isolated via dedicated helpers (`_get_quiz_results_worksheet`, `_save_quiz_result`, `_display_quiz_results`) to separate it from ABC worksheet operations.
- `gs_load_node` includes defensive behavior to avoid overwriting in-memory edits when no `to_set` payload is present.

---

## F) Quick Improvement Opportunities (Function-Level)

- Centralize repeated Google auth/open code into one helper (e.g., `open_spreadsheet_from_cfg(cfg)`).
- Split `main()` into per-choice handlers (`handle_choice_1`, `handle_choice_2`, etc.) for easier testing.
- Add docstrings to nested helpers for consistency.
- Optionally add a lightweight call-map section in docs after future refactor.
