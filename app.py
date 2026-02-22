"""Simple LangGraph CLI that preloads key/value pairs into the graph state.

Run:
    pip install -r requirements.txt
    python app.py              # prints the preloaded abc store
    python app.py --set color blue  # sets a key then prints the store

This example uses a StateGraph with a small "abc" dict stored in state.
"""
from typing import Dict
from typing_extensions import TypedDict
import argparse
import random
from urllib.parse import quote_plus
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from langgraph.graph import START, StateGraph
import os
from datetime import datetime
import shutil

# Global config for Google Sheets (workaround for state persistence)
_gs_config_global = None


def _center_print(text: str = "", indent: int = 0) -> None:
    """Print text centered in the terminal."""
    import re
    try:
        width = shutil.get_terminal_size().columns
    except:
        width = 80
    
    lines = text.split('\n') if text else ['']
    for line in lines:
        # Add indent spaces to the line content
        line_with_indent = ' ' * indent + line
        # Remove ANSI escape codes to calculate visual length
        visual_length = len(re.sub(r'\033\[[0-9;]*m', '', line_with_indent))
        # Calculate padding to center the line
        padding = max(0, (width - visual_length) // 2)
        print(' ' * padding + line_with_indent)


def _center_input(prompt: str = "") -> str:
    """Display centered prompt and get input."""
    import re
    try:
        width = shutil.get_terminal_size().columns
    except:
        width = 80
    
    # Remove ANSI escape codes to calculate visual length
    visual_length = len(re.sub(r'\033\[[0-9;]*m', '', prompt))
    padding = max(0, (width - visual_length) // 2)
    return input(' ' * padding + prompt)


def _get_quiz_results_worksheet(spreadsheet):
    """Get or create the quiz results worksheet."""
    try:
        ws = spreadsheet.worksheet("Quiz Results")
        return ws
    except Exception:
        # Create the worksheet with headers
        ws = spreadsheet.add_worksheet(title="Quiz Results", rows=1000, cols=3)
        # Add headers
        ws.update([["Timestamp", "Worksheet", "Status"]], range_name="A1:C1")
        return ws


def _save_quiz_result(spreadsheet, worksheet_name: str, status: str = "Completed"):
    """Save a quiz completion result to the Quiz Results worksheet."""
    try:
        ws = _get_quiz_results_worksheet(spreadsheet)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Append the result to the worksheet
        ws.append_row([timestamp, worksheet_name, status])
    except Exception as e:
        print(f"Failed to save quiz result: {e}")


def _display_quiz_results(spreadsheet):
    """Display all quiz results from the Quiz Results worksheet."""
    try:
        ws = _get_quiz_results_worksheet(spreadsheet)
        all_values = ws.get_all_values()
        if not all_values or len(all_values) < 2:
            print("No quiz results yet.")
            return
        
        print('\033[2J\033[H', end='', flush=True)
        _center_print('\033[1mQuiz Results\033[0m')
        _center_print()
        
        # Display header
        headers = all_values[0]
        _center_print(f"{headers[0]:<25} {headers[1]:<30} {headers[2]:<15}")
        _center_print("-" * 70)
        
        # Display results in reverse order (newest first)
        for row in reversed(all_values[1:]):
            if len(row) >= 3:
                timestamp = row[0][:19] if len(row[0]) > 19 else row[0]
                worksheet = row[1][:28] if len(row[1]) > 28 else row[1]
                status = row[2][:13] if len(row[2]) > 13 else row[2]
                _center_print(f"{timestamp:<25} {worksheet:<30} {status:<15}")
        
        _center_print()
    except Exception as e:
        print(f"Failed to display quiz results: {e}")


def _next_worksheet_name(spreadsheet, base_name: str) -> str:
    existing_titles = {ws.title for ws in spreadsheet.worksheets()}
    if base_name not in existing_titles:
        return base_name
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = f"{base_name}_{stamp}"
    if candidate not in existing_titles:
        return candidate
    suffix = 1
    while True:
        candidate = f"{base_name}_{stamp}_{suffix}"
        if candidate not in existing_titles:
            return candidate
        suffix += 1


def _open_target_worksheet(spreadsheet, base_name: str, allow_overwrite: bool):
    if allow_overwrite:
        try:
            ws = spreadsheet.worksheet(base_name)
            return ws, base_name
        except Exception:
            _center_print(f'Create new worksheet "{base_name}"?')
            confirm = _center_input('(yes/no): ').strip().lower()
            if confirm not in ['yes', 'y']:
                return None, None
            ws = spreadsheet.add_worksheet(title=base_name, rows=100, cols=2)
            return ws, base_name

    worksheet_name = _next_worksheet_name(spreadsheet, base_name)
    _center_print(f'Create new worksheet "{worksheet_name}"?')
    confirm = _center_input('(yes/no): ').strip().lower()
    if confirm not in ['yes', 'y']:
        return None, None
    ws = spreadsheet.add_worksheet(title=worksheet_name, rows=100, cols=2)
    return ws, worksheet_name


def _resolve_spreadsheet_title(cfg: dict) -> str | None:
    if cfg.get("spreadsheet_title"):
        return cfg.get("spreadsheet_title")
    if not cfg.get("creds") or not cfg.get("spreadsheet"):
        return None
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(cfg["creds"], scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_key(cfg["spreadsheet"])
        title = sh.title
        cfg["spreadsheet_title"] = title
        return title
    except Exception:
        return None


def fetch_related_items(query: str, limit: int = 20) -> list[str]:
    """Fetch first N place names from Google Maps search results."""
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        encoded_query = quote_plus(query)
        print(f"Navigating to Google Maps search for: {query}")
        print(f"Encoded query: {encoded_query}")
        maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_query}"
        print(f"Maps URL: {maps_url}")
        driver.get(maps_url)

        import time
        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        items: list[str] = []
        seen: set[str] = set()

        blocked_tokens = {
            "directions",
            "website",
            "call",
            "share",
            "save",
            "nearby",
            "send to your phone",
            "view all",
            "google maps",
            "open now",
            "closed",
            "sponsored",
        }

        def is_valid_place_name(name: str) -> bool:
            normalized = " ".join(name.split()).strip()
            if len(normalized) < 2 or len(normalized) > 120:
                return False
            low = normalized.casefold()
            if any(token in low for token in blocked_tokens):
                return False
            if any(ch in normalized for ch in ("$", "€", "£")):
                return False
            if normalized.replace(" ", "").isdigit():
                return False
            return True

        def collect_place_names() -> None:
            place_links = driver.find_elements(By.XPATH, "//div[@role='feed']//a[contains(@href, '/maps/place')]")
            if not place_links:
                place_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/maps/place')]")
            for link in place_links:
                if len(items) >= limit:
                    return
                raw = (link.get_attribute("aria-label") or link.text or "").strip()
                if not raw:
                    continue
                name = raw.split("\n", 1)[0].strip()
                if not is_valid_place_name(name):
                    continue
                if name not in seen:
                    seen.add(name)
                    items.append(name)

        feed = None
        try:
            feed = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='feed']")))
        except Exception:
            feed = None

        stagnation = 0
        previous_count = -1
        for _ in range(45):
            collect_place_names()
            if len(items) >= limit:
                break

            if len(items) == previous_count:
                stagnation += 1
            else:
                stagnation = 0
                previous_count = len(items)

            if stagnation >= 6:
                break

            if feed is not None:
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].clientHeight;", feed)
            else:
                driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(0.6)

        collect_place_names()
        return items[:limit]
    
    except Exception as e:
        print(f"Chrome Maps search error: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    finally:
        if driver:
            driver.quit()


class State(TypedDict):
    abc: Dict[str, str]
    # optional helper key used only when invoking set via CLI
    to_set: Dict[str, str]


def set_abc(state: State) -> dict:
    """If `to_set` present, merge it into `abc` and return updated state."""
    #PRINT001 - print("--- in set_abc node ---" )
    abc = dict(state.get("abc", {}))
    to_set = state.get("to_set") or {}
    if to_set:
        abc.update(to_set)
    return {
        "abc": abc,
        "_gs_config": state.get("_gs_config"),
    }


def show_abc(state: State) -> dict:
    """Return state without changes (we'll print result after invoke)."""
    #PRINT002 - print("--- in show_abc node ---")
    return {
        "abc": state.get("abc", {}),
        "_gs_config": state.get("_gs_config"),
    }


def interactive_set(state: State) -> dict:
    """No-op placeholder — interactive input is handled in `main()`."""
    #PRINT003 - print("--- in interactive_set node ---")
    return dict(state)


def gs_load_node(state: State) -> dict:
    """Load key/value pairs from a Google Sheets worksheet into `kv`.

    Expects `_gs_config` in state with keys: `creds` (path to service account
    JSON) and `spreadsheet` (spreadsheet ID), optional `worksheet`.
    
    If abc is already populated in state, skip loading from sheets.
    """
    global _gs_config_global
    cfg = _gs_config_global or {}
    
    # If state has abc data with content and no to_set, skip loading from sheets
    # This preserves modifications made in the current flow (like deletions)
    # If to_set is present, always load and merge.
    existing_abc = state.get("abc", {})
    to_set = state.get("to_set")
    if existing_abc and not to_set:
        return {
            "abc": existing_abc,
            "_gs_config": state.get("_gs_config"),
        }
    
    if not cfg.get("creds") or not cfg.get("spreadsheet"):
        return {
            "abc": state.get("abc", {}),
            "_gs_config": state.get("_gs_config"),
        }
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(cfg["creds"], scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_key(cfg["spreadsheet"])
        
        # Try to get configured worksheet, fall back to first worksheet if not configured
        worksheet_name = cfg.get("worksheet")
        if worksheet_name is not None and worksheet_name != "":
            try:
                ws = sh.worksheet(worksheet_name)
            except Exception:
                # If configured worksheet doesn't exist, use the first one
                ws = sh.worksheets()[0]
                worksheet_name = ws.title
                # Update global config with the actual worksheet name
                _gs_config_global["worksheet"] = worksheet_name
                cfg["worksheet"] = worksheet_name
        else:
            # If no worksheet configured, always use the first one
            ws = sh.worksheets()[0]
            worksheet_name = ws.title
            # Update global config with the actual worksheet name
            _gs_config_global["worksheet"] = worksheet_name
            cfg["worksheet"] = worksheet_name
            
        rows = ws.get_all_values()
        abc = dict(state.get("abc", {}))
        for row in rows:
            if not row:
                continue
            if len(row) >= 2 and row[0].strip():
                key = row[0].strip()
                value = row[1]
                if key.casefold() == "key" and str(value).strip().casefold() == "value":
                    continue
                abc[key] = value
        return {
            "abc": abc,
            "_gs_config": state.get("_gs_config"),
        }
    except Exception as e:
        print("Warning: failed to load from Google Sheets:", e)
        return {
            "abc": state.get("abc", {}),
            "_gs_config": state.get("_gs_config"),
        }


def gs_save_node(state: State) -> dict:
    """Save the `kv` dict into the configured Google Sheets worksheet.

    By default it writes to a new worksheet tab to avoid overwriting.
    Explicit overwrite config can reuse the configured worksheet name.
    Requires `_gs_config` in state.
    """
    global _gs_config_global
    #PRINT008 - print("--- in gs_save_node ---")
    #PRINT009 - print("state in gs_save_node:", state)
    cfg = _gs_config_global or {}
    if not cfg.get("creds") or not cfg.get("spreadsheet"):
        print("No Google Sheets config provided; skipping save.")
        return {
            "abc": state.get("abc", {}),
            "_gs_config": state.get("_gs_config"),
        }
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(cfg["creds"], scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_key(cfg["spreadsheet"])
        allow_overwrite = bool(cfg.get("overwrite", False))
        force_current_worksheet = bool(state.get("_force_current_worksheet", False))
        base_name = cfg.get("worksheet", "Sheet1")

        if force_current_worksheet:
            try:
                ws = sh.worksheet(base_name)
            except Exception:
                # If overwrite is allowed, auto-create without prompting
                if allow_overwrite:
                    ws = sh.add_worksheet(title=base_name, rows=100, cols=2)
                else:
                    _center_print(f'Create new worksheet "{base_name}"?')
                    confirm = _center_input('(yes/no): ').strip().lower()
                    if confirm not in ['yes', 'y']:
                        print('Cancelled.')
                        return {"abc": state.get("abc", {}), "_gs_config": state.get("_gs_config")}
                    ws = sh.add_worksheet(title=base_name, rows=100, cols=2)
            target_name = base_name
            should_clear_before_write = True
        else:
            ws, target_name = _open_target_worksheet(sh, base_name, allow_overwrite)
            if ws is None:
                print('Cancelled.')
                return {"abc": state.get("abc", {}), "_gs_config": state.get("_gs_config")}
            should_clear_before_write = allow_overwrite

        abc = dict(state.get("abc", {}))
        rows = [[k, v] for k, v in abc.items()]
        if should_clear_before_write:
            ws.clear()
        ws.update(values=rows, range_name="A1")
        _gs_config_global["worksheet"] = target_name
        print(f'Saved ABC to Google Sheet worksheet: {target_name}')
        return {
            "abc": abc,
            "_gs_config": state.get("_gs_config"),
        }
    except Exception as e:
        import traceback
        print("Warning: failed to save to Google Sheets:", e)
        print("Traceback:", traceback.format_exc())
        return {
            "abc": state.get("abc", {}),
            "_gs_config": state.get("_gs_config"),
        }


def build_graph() -> StateGraph:
    #PRINT010 - print("--- building graph ---")
    graph = StateGraph(State)
    # nodes
    graph.add_node("gs_load", gs_load_node)
    graph.add_node("set_abc", set_abc)
    graph.add_node("gs_save", gs_save_node)
    graph.add_node("show_abc", show_abc)

    # linear flow: START -> gs_load -> set_kv -> gs_save -> show_kv
    graph.add_edge(START, "gs_load")
    graph.add_edge("gs_load", "set_abc")
    graph.add_edge("set_abc", "gs_save")
    graph.add_edge("gs_save", "show_abc")
    return graph


def main():
    #PRINT011 - print("--- starting main ---")
    global _gs_config_global
    load_dotenv()

    #PRINT018 - print("---CLI Arguments---")
    parser = argparse.ArgumentParser(description="LangGraph ABC starter app")
    parser.add_argument("--gs-creds", help="path to Google service account JSON credentials")
    parser.add_argument("--gs-sheet", help="Google Sheets spreadsheet ID to load/save")
    parser.add_argument("--gs-worksheet", help="worksheet name (default: Sheet1)")
    parser.add_argument("--gs-overwrite", action="store_true", help="explicitly allow overwriting the target worksheet")
    args = parser.parse_args()
    
    # Check for command line args first, then fall back to environment variables
    gs_creds = args.gs_creds or os.getenv("GS_CREDS")
    gs_sheet = args.gs_sheet or os.getenv("GS_SHEET")
    gs_worksheet = args.gs_worksheet or os.getenv("GS_WORKSHEET")
    gs_overwrite_raw = os.getenv("GS_OVERWRITE", "")
    gs_overwrite = args.gs_overwrite or gs_overwrite_raw.strip().casefold() in {"1", "true", "yes", "y", "overwrite"}
    
    if gs_creds and gs_sheet:
        # If worksheet is not explicitly set, we'll let gs_load_node handle getting the first one
        # No need to try to load it during initialization
        
        _gs_config_global = {
            "creds": gs_creds,
            "spreadsheet": gs_sheet,
            "worksheet": gs_worksheet,
            "overwrite": gs_overwrite,
        }
    #PRINT017 -print("_gs_config_global:", _gs_config_global)

    # Define table display function
    def _print_fixed_keys_values(d: dict, fixed_keys: list[str], cols: int = 4) -> None:
        _center_print()
        if not fixed_keys:
            _center_print("(empty)")
            return
        groups = [
            [chr(code) for code in range(ord('A'), ord('G') + 1)],
            [chr(code) for code in range(ord('H'), ord('N') + 1)],
            [chr(code) for code in range(ord('O'), ord('T') + 1)],
            [chr(code) for code in range(ord('U'), ord('Z') + 1)],
        ]
        printed_any = False
        for group in groups:
            lines = []
            for key in group:
                value = str(d.get(key, "")).strip()
                if value:
                    lines.append(f"{key}: \033[93m{value}\033[0m")
            if not lines:
                continue
            if printed_any:
                _center_print()
            for line in lines:
                _center_print(line)
            printed_any = True
        if not printed_any:
            _center_print("(empty)")

    # Interactive prompt handled in main (always interactive)
    interactive_pairs = {}
    fixed_keys = [chr(ord('A') + i) for i in range(26)]
    
    # Initialize worksheet selection on startup if not already set
    worksheet_name = _gs_config_global.get("worksheet") if _gs_config_global else None
    if _gs_config_global and _gs_config_global.get("spreadsheet") and not worksheet_name:
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(_gs_config_global["creds"], scopes=scopes)
            client = gspread.authorize(creds)
            sh = client.open_by_key(_gs_config_global["spreadsheet"])
            first_ws = sh.worksheets()[0]  # Get first worksheet by index
            _gs_config_global["worksheet"] = first_ws.title
        except Exception as e:
            print(f"Failed to initialize worksheet on startup: {e}")
    
    while True:
        # Clear screen
        print('\033[2J\033[H', end='', flush=True)
        
        cfg = _gs_config_global or {}
        active_sheet_id = cfg.get("spreadsheet")
        active_worksheet = cfg.get("worksheet")
        active_sheet_title = _resolve_spreadsheet_title(cfg) if active_sheet_id else None

        # Count total worksheets
        total_worksheets = 0
        if active_sheet_id and cfg.get("creds"):
            try:
                import gspread
                from google.oauth2.service_account import Credentials
                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]
                creds = Credentials.from_service_account_file(cfg["creds"], scopes=scopes)
                client = gspread.authorize(creds)
                sh = client.open_by_key(active_sheet_id)
                total_worksheets = len(sh.worksheets())
            except Exception:
                total_worksheets = 0

        _center_print()
        _center_print('\033[1mM   E   N   U\033[0m')
        _center_print()
        if active_sheet_id:
            worksheet_label = active_worksheet or "(default)"
            sheet_label = active_sheet_title or active_sheet_id
            _center_print("-----------------------------------------------------")
            _center_print(f'Active Google Sheet: \033[93m{sheet_label}\033[0m | Worksheet: \033[93m{worksheet_label}\033[0m')
            if total_worksheets > 0:
                _center_print(f'Total Worksheets: {total_worksheets}')
            _center_print("-----------------------------------------------------")
        else:
            _center_print('Active Google Sheet: not configured')
        _center_print()
        _center_print('1. List Worksheets')
        _center_print('2. Select Worksheet')
        _center_print('3. Delete Worksheet')
        _center_print('4. Rename Worksheet')
        _center_print()
        _center_print('5. Create ABC')
        _center_print('6. Read ABC')
        _center_print('7. Update ABC')
        _center_print('8. Delete ABC')
        _center_print()
        _center_print('9. Quiz')
        _center_print('10. Quiz Results')
        _center_print()
        _center_print()
        _center_print()
        try:
            choice = _center_input('Choose option (1-10): ').strip()
        except EOFError:
            break
        if not choice:
            _center_print('Please choose option 1-10.')
            continue
        if choice == '5':
            # Create a new GS_WORKSHEET with A-Z keys (formerly choice 3: Import ABC)
            print('\033[2J\033[H', end='', flush=True)
            cfg = _gs_config_global or {}
            if not cfg.get("creds") or not cfg.get("spreadsheet"):
                print('Google Sheets config missing. Set GS_CREDS and GS_SHEET (and GS_WORKSHEET).')
                continue

            try:
                import gspread
                from google.oauth2.service_account import Credentials

                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]
                creds = Credentials.from_service_account_file(cfg["creds"], scopes=scopes)
                client = gspread.authorize(creds)
                sh = client.open_by_key(cfg["spreadsheet"])

                # If no worksheet configured, use the first existing worksheet
                base_name = cfg.get("worksheet")
                if not base_name:
                    # Use the first worksheet already in the spreadsheet
                    existing_worksheets = sh.worksheets()
                    if existing_worksheets:
                        ws = existing_worksheets[0]
                        worksheet_name = ws.title
                    else:
                        # If spreadsheet is empty, create a default Sheet1
                        _center_print('Create new worksheet "Sheet1"?')
                        confirm = _center_input('(yes/no): ').strip().lower()
                        if confirm not in ['yes', 'y']:
                            print('Cancelled.')
                            continue
                        ws = sh.add_worksheet(title="Sheet1", rows=100, cols=21)
                        worksheet_name = "Sheet1"
                    allow_overwrite = True  # Always overwrite when using existing worksheet
                else:
                    allow_overwrite = bool(cfg.get("overwrite", False))
                    ws, worksheet_name = _open_target_worksheet(sh, base_name, allow_overwrite)
                    if ws is None:
                        print('Cancelled.')
                        continue
                
                ws.resize(rows=100, cols=21)

                rows = [[chr(ord('A') + i), ""] for i in range(26)]
                if allow_overwrite:
                    ws.clear()
                ws.update(values=rows, range_name="A1")
                _gs_config_global["worksheet"] = worksheet_name
                print(f'Ready GS_WORKSHEET "{worksheet_name}" with keys A-Z.')

                topic = input('Enter your Google Maps search query: ').strip()
                if not topic:
                    print('No topic entered. Skipping extraction.')
                    continue

                try:
                    print(f'Searching Google Maps for "{topic}" and extracting place names...')
                    items = fetch_related_items(topic, limit=20)
                except Exception as e:
                    print('Failed to fetch internet items:', e)
                    continue

                if not items:
                    print('No related items found.')
                    continue

                items = sorted(items, key=lambda name: name.casefold())

                print(f'Found {len(items)} related item(s):')
                for index, item in enumerate(items, start=1):
                    print(f'{index}. {item}')

                ordered_keys = [chr(ord('A') + i) for i in range(26)]
                letter_groups: dict[str, list[str]] = {key: [] for key in ordered_keys}
                unmatched_items: list[str] = []

                for item in items:
                    first_letter = ""
                    for ch in item.strip():
                        if ch.isalpha():
                            first_letter = ch.upper()
                            break
                    if first_letter in letter_groups:
                        letter_groups[first_letter].append(item)
                    else:
                        unmatched_items.append(item)

                max_items_per_letter = max((len(letter_groups[key]) for key in ordered_keys), default=0)
                value_column_count = max(1, max_items_per_letter)

                aligned_rows = []
                for key in ordered_keys:
                    values = letter_groups[key]
                    padded_values = values + [""] * (value_column_count - len(values))
                    aligned_rows.append([key] + padded_values)

                if allow_overwrite:
                    ws.clear()
                ws.update(values=aligned_rows, range_name="A1")
                try:
                    used_columns = 1 + value_column_count
                    sh.batch_update({
                        "requests": [
                            {
                                "autoResizeDimensions": {
                                    "dimensions": {
                                        "sheetId": ws.id,
                                        "dimension": "COLUMNS",
                                        "startIndex": 0,
                                        "endIndex": used_columns,
                                    }
                                }
                            }
                        ]
                    })
                except Exception as resize_error:
                    print(f'Warning: could not auto-resize columns: {resize_error}')
                print('Added extracted items to A-Z keys with each matched item in a separate column.')
                if unmatched_items:
                    print(f'Skipped {len(unmatched_items)} item(s) that did not start with a letter.')
                input('\nPress ENTER to return to menu...')
            except Exception as e:
                print('Failed to initialize GS_WORKSHEET:', e)
        elif choice == '6':
            # Read ABC table (read-only)
            print('\033[2J\033[H', end='', flush=True)
            loaded = gs_load_node({"abc": {}})
            _print_fixed_keys_values(loaded.get("abc", {}), fixed_keys, cols=4)
            input('\nPress ENTER to return to menu...')
        elif choice == '7':
            # Update ABC
            print('\033[2J\033[H', end='', flush=True)
            loaded = gs_load_node({"abc": {}})
            editable_abc = dict(loaded.get("abc", {}))
            available_keys = [
                key for key, value in editable_abc.items()
                if str(value).strip()
            ]
            available_keys.sort(key=lambda key: key.casefold())

            if not available_keys:
                print('No non-blank keys available to edit in the current worksheet.')
                continue

            print('Available keys to edit:')
            for idx, key in enumerate(available_keys, start=1):
                current_value = str(editable_abc.get(key, ""))
                print(f' {idx}. {key}: \033[93m{current_value}\033[0m')

            pending_pairs = {}
            while True:
                try:
                    key_choice = input('Select key number or exact key (blank to finish): ').strip()
                except EOFError:
                    break
                if not key_choice:
                    break

                selected_key = None
                if key_choice.isdigit():
                    selected_index = int(key_choice)
                    if 1 <= selected_index <= len(available_keys):
                        selected_key = available_keys[selected_index - 1]
                if selected_key is None:
                    for key in available_keys:
                        if key.casefold() == key_choice.casefold():
                            selected_key = key
                            break
                if selected_key is None:
                    print('Invalid key selection. Choose a listed number or key name.')
                    continue

                current_value = str(editable_abc.get(selected_key, ""))
                print(f'Current value for "{selected_key}": \033[93m{current_value}\033[0m')
                try:
                    val = input(f'New value for "{selected_key}": ').strip()
                except EOFError:
                    val = ""
                pending_pairs[selected_key] = val
                interactive_pairs[selected_key] = val
                editable_abc[selected_key] = val

            if pending_pairs:
                temp_state = {
                    "abc": {},
                    "to_set": pending_pairs,
                    "_force_current_worksheet": True,
                }
                # Temporarily set overwrite to True to avoid prompts
                original_overwrite = _gs_config_global.get("overwrite", False)
                _gs_config_global["overwrite"] = True
                
                graph = build_graph()
                compiled = graph.compile()
                compiled.invoke(temp_state)
                
                # Restore original overwrite setting
                _gs_config_global["overwrite"] = original_overwrite
                
                print('Saved your edits.')
            else:
                print('No edits to save.')
            input('\nPress ENTER to return to menu...')
        elif choice == '8':
            # Delete ABC value
            print('\033[2J\033[H', end='', flush=True)
            loaded = gs_load_node({"abc": {}})
            deletable_abc = dict(loaded.get("abc", {}))

            if not deletable_abc:
                print('No data available in the current worksheet.')
                continue

            continue_deleting = True
            while continue_deleting:
                # Get available keys with non-blank values
                available_keys = [
                    key for key, value in deletable_abc.items()
                    if str(value).strip()
                ]
                available_keys.sort(key=lambda key: key.casefold())

                if not available_keys:
                    print('No non-blank keys available to delete in the current worksheet.')
                    break

                print('\nAvailable keys to delete:')
                for idx, key in enumerate(available_keys, start=1):
                    current_value = str(deletable_abc.get(key, ""))
                    print(f' {idx}. {key}: \033[93m{current_value}\033[0m')

                try:
                    key_choice = input('Select key number or exact key to delete (blank to cancel): ').strip()
                except EOFError:
                    break
                if not key_choice:
                    break

                selected_key = None
                if key_choice.isdigit():
                    selected_index = int(key_choice)
                    if 1 <= selected_index <= len(available_keys):
                        selected_key = available_keys[selected_index - 1]
                if selected_key is None:
                    for key in available_keys:
                        if key.casefold() == key_choice.casefold():
                            selected_key = key
                            break
                if selected_key is None:
                    print('Invalid key selection. No key deleted.')
                    continue

                try:
                    confirm = input(f'Confirm delete "{selected_key}"? (yes/no): ').strip().casefold()
                except EOFError:
                    confirm = "no"
                if confirm not in {"yes", "y"}:
                    print('Delete canceled.')
                    continue

                # Set the value to empty string (keep the key)
                deletable_abc[selected_key] = ""
                
                # Save the modified data back to the current worksheet with overwrite
                temp_state = {
                    "abc": deletable_abc,
                    "_force_current_worksheet": True,
                }
                # Temporarily set overwrite to True to avoid prompts
                original_overwrite = _gs_config_global.get("overwrite", False)
                _gs_config_global["overwrite"] = True
                
                graph = build_graph()
                compiled = graph.compile()
                compiled.invoke(temp_state)
                
                # Restore original overwrite setting
                _gs_config_global["overwrite"] = original_overwrite
                
                print(f'Deleted value for "{selected_key}".')
                
                # Show the updated list of available keys
                updated_available_keys = [
                    key for key, value in deletable_abc.items()
                    if str(value).strip()
                ]
                updated_available_keys.sort(key=lambda key: key.casefold())
                
                if updated_available_keys:
                    print('\nUpdated available keys:')
                    for idx, key in enumerate(updated_available_keys, start=1):
                        current_value = str(deletable_abc.get(key, ""))
                        print(f' {idx}. {key}: \033[93m{current_value}\033[0m')
                
                # Ask if user wants to continue deleting
                try:
                    continue_choice = input('\nDelete another value? (yes/no): ').strip().casefold()
                except EOFError:
                    continue_deleting = False
                    
                if continue_choice not in {"yes", "y"}:
                    continue_deleting = False

            input('\nPress ENTER to return to menu...')
        elif choice == '9':
            # Quiz: ask a random question from current state data
            print('\033[2J\033[H', end='', flush=True)
            loaded = gs_load_node({"abc": {}})
            quiz_abc = dict(loaded.get("abc", {}))
            if interactive_pairs:
                quiz_abc.update(interactive_pairs)

            def _print_quiz_graph_for_review() -> None:
                _center_print('--- Quiz Graph Review ---')
                populated_items = [
                    (k, v) for k, v in quiz_abc.items()
                    if str(v).strip()
                ]
                if not populated_items:
                    _center_print('(empty)')
                    return
                for key, value in sorted(populated_items, key=lambda kv: kv[0].casefold()):
                    _center_print(f'{key}: \033[93m{value}\033[0m')

            candidates = [(k, v) for k, v in quiz_abc.items() if str(v).strip()]
            if not candidates:
                _center_print('No quiz questions available. Add data first.')
                continue

            # Practice mode: show each key-value pair one at a time
            practice_keys = sorted([k for k, v in candidates], key=lambda x: x.casefold())
            print('\033[2J\033[H', end='', flush=True)
            _center_print('\033[94m' + '=' * 50 + '\033[0m')
            _center_print('\033[94m\033[1mPRACTICE MODE\033[0m')
            _center_print('\033[94m' + '=' * 50 + '\033[0m')
            _center_print()
            print(f'Practice Mode - Learn the {len(practice_keys)} key-value pairs')
            input('Press ENTER to start practice...')
            
            for idx, key in enumerate(practice_keys, start=1):
                print('\033[2J\033[H', end='', flush=True)
                value = quiz_abc[key]
                _center_print(f'Practice ({idx}/{len(practice_keys)})')
                _center_print()
                _center_print(f'Key: \033[1m{key}\033[0m')
                _center_print(f'Value: \033[93m{value}\033[0m')
                
                if idx < len(practice_keys):
                    _center_input('Press ENTER to continue...')
                else:
                    _center_input('Press ENTER to start the real quiz...')

            remaining = {k: v for k, v in candidates}
            required_repeats = {k: 1 for k in remaining}
            correct_streaks = {k: 0 for k in remaining}
            consecutive_incorrect_count = 0
            print('\033[2J\033[H', end='', flush=True)
            _center_print('\033[94m' + '=' * 50 + '\033[0m')
            _center_print('\033[94m\033[1mQUIZ\033[0m')
            _center_print('\033[94m' + '=' * 50 + '\033[0m')
            _center_print()
            _center_print(f'Starting quiz with {len(remaining)} question(s).')
            _center_input('Press ENTER to start...')
            while remaining:
                print('\033[2J\033[H', end='', flush=True)
                question_key = random.choice(list(remaining.keys()))
                expected_value = remaining[question_key]
                required = required_repeats[question_key]
                streak = correct_streaks[question_key]

                try:
                    answer = _center_input(
                        f'Quiz - What is the value for "{question_key}"? '
                        f'({streak + 1}/{required}) '
                    ).strip()
                except EOFError:
                    _center_print('Quiz canceled.')
                    break

                if answer.casefold() == str(expected_value).strip().casefold():
                    streak += 1
                    correct_streaks[question_key] = streak
                    consecutive_incorrect_count = 0
                    _center_print(f'\033[92mCorrect\033[0m! {len(remaining) - 1} remaining.')
                else:
                    consecutive_incorrect_count += 1
                    required = max(2, required * 2)
                    required_repeats[question_key] = required
                    correct_streaks[question_key] = 0
                    _center_print(f'\033[91mIncorrect\033[0m. Correct value is: \033[93m{expected_value}\033[0m')
                    _center_print(
                        f'You must now answer "{question_key}" correctly '
                        f'{required} times in a row.'
                    )
                    if consecutive_incorrect_count >= 3:
                        _print_quiz_graph_for_review()
                        consecutive_incorrect_count = 0

                if question_key in remaining and correct_streaks[question_key] >= required:
                    del remaining[question_key]
                    del required_repeats[question_key]
                    del correct_streaks[question_key]
                
                if remaining:
                    _center_input('Press ENTER to continue to next question...')

            if not remaining:
                _center_print('Great job! You answered all populated keys correctly.')
                final_keys = sorted(k for k, _ in candidates)
                canceled_final = False
                final_consecutive_incorrect_count = 0
                print('\033[2J\033[H', end='', flush=True)
                _center_print('\033[94m' + '=' * 50 + '\033[0m')
                _center_print('\033[94m\033[1mFINAL QUIZ\033[0m')
                _center_print('\033[94m\033[1mAnswer all keys correctly in alphabetical order\033[0m')
                _center_print('\033[94m' + '=' * 50 + '\033[0m')
                _center_print()
                _center_input('Press ENTER to start final quiz...')
                while True:
                    failed = False
                    for index, question_key in enumerate(final_keys, start=1):
                        print('\033[2J\033[H', end='', flush=True)
                        expected_value = quiz_abc[question_key]
                        try:
                            answer = _center_input(
                                f'Final quiz ({index}/{len(final_keys)}) - '
                                f'What is the value for "{question_key}"? '
                            ).strip()
                        except EOFError:
                            _center_print('Final quiz canceled.')
                            canceled_final = True
                            failed = True
                            break

                        if answer.casefold() != str(expected_value).strip().casefold():
                            final_consecutive_incorrect_count += 1
                            _center_print(f'\033[91mIncorrect\033[0m. Correct value is: \033[93m{expected_value}\033[0m')
                            if final_consecutive_incorrect_count >= 3:
                                _print_quiz_graph_for_review()
                                final_consecutive_incorrect_count = 0
                            _center_print('Restarting final quiz from the beginning.')
                            _center_input('Press ENTER to restart...')
                            failed = True
                            break
                        else:
                            final_consecutive_incorrect_count = 0
                            _center_print(f'\033[92mCorrect\033[0m!')
                            if index < len(final_keys):
                                _center_input('Press ENTER to continue...')

                    if canceled_final:
                        break
                    if not failed:
                        print('\033[2J\033[H', end='', flush=True)
                        _center_print()
                        _center_print('\033[92m\033[1mCongratulations!\033[0m')
                        _center_print()
                        _center_print('\033[92mYou have finished the quiz!\033[0m')
                        _center_print()
                        _center_print('\033[92mYour results will be saved and can be viewed in Choice 10.\033[0m')
                        _center_print()
                        # Save quiz result
                        cfg = _gs_config_global or {}
                        if cfg.get("creds") and cfg.get("spreadsheet"):
                            try:
                                import gspread
                                from google.oauth2.service_account import Credentials
                                scopes = [
                                    "https://www.googleapis.com/auth/spreadsheets",
                                    "https://www.googleapis.com/auth/drive",
                                ]
                                creds = Credentials.from_service_account_file(cfg["creds"], scopes=scopes)
                                client = gspread.authorize(creds)
                                sh = client.open_by_key(cfg["spreadsheet"])
                                worksheet_name = cfg.get("worksheet", "(default)")
                                _save_quiz_result(sh, worksheet_name, "Completed")
                            except Exception:
                                pass
                        break
            _center_input('Press ENTER to return to menu...')
        elif choice == '10':
            print('\033[2J\033[H', end='', flush=True)
            cfg = _gs_config_global or {}
            if not cfg.get("creds") or not cfg.get("spreadsheet"):
                print('Google Sheets config missing. Set GS_CREDS and GS_SHEET (and GS_WORKSHEET).')
                input('Press ENTER to return to menu...')
                continue

            try:
                import gspread
                from google.oauth2.service_account import Credentials

                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]
                creds = Credentials.from_service_account_file(cfg["creds"], scopes=scopes)
                client = gspread.authorize(creds)
                sh = client.open_by_key(cfg["spreadsheet"])
                _display_quiz_results(sh)
                input('Press ENTER to return to menu...')
            except Exception as e:
                print('Failed to display quiz results:', e)
                input('Press ENTER to return to menu...')
        elif choice == '1':
            print('\033[2J\033[H', end='', flush=True)
            cfg = _gs_config_global or {}
            if not cfg.get("creds") or not cfg.get("spreadsheet"):
                print('Google Sheets config missing. Set GS_CREDS and GS_SHEET (and GS_WORKSHEET).')
                continue

            try:
                import gspread
                from google.oauth2.service_account import Credentials

                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]
                creds = Credentials.from_service_account_file(cfg["creds"], scopes=scopes)
                client = gspread.authorize(creds)
                sh = client.open_by_key(cfg["spreadsheet"])
                active_worksheet = cfg.get("worksheet")
                worksheets = sh.worksheets()

                print("Worksheets:")
                for idx, ws in enumerate(worksheets, start=1):
                    marker = "*" if ws.title == active_worksheet else " "
                    print(f' {idx}. {marker} {ws.title}')
                input('\nPress ENTER to return to menu...')
            except Exception as e:
                print('Failed to list worksheets:', e)
        elif choice == '2':
            print('\033[2J\033[H', end='', flush=True)
            cfg = _gs_config_global or {}
            if not cfg.get("creds") or not cfg.get("spreadsheet"):
                print('Google Sheets config missing. Set GS_CREDS and GS_SHEET (and GS_WORKSHEET).')
                continue

            try:
                import gspread
                from google.oauth2.service_account import Credentials

                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]
                creds = Credentials.from_service_account_file(cfg["creds"], scopes=scopes)
                client = gspread.authorize(creds)
                sh = client.open_by_key(cfg["spreadsheet"])
                active_worksheet = cfg.get("worksheet")
                worksheets = sh.worksheets()

                print("Select Worksheet:")
                for idx, ws in enumerate(worksheets, start=1):
                    marker = "*" if ws.title == active_worksheet else " "
                    print(f' {idx}. {marker} {ws.title}')

                selection = input(
                    'Select worksheet by number or exact name (Enter to keep current): '
                ).strip()
                if not selection:
                    continue

                selected_title = None
                if selection.isdigit():
                    selected_index = int(selection)
                    if 1 <= selected_index <= len(worksheets):
                        selected_title = worksheets[selected_index - 1].title
                if selected_title is None:
                    for ws in worksheets:
                        if ws.title == selection:
                            selected_title = ws.title
                            break

                if not selected_title:
                    print('Invalid selection. Active worksheet unchanged.')
                    continue

                _gs_config_global["worksheet"] = selected_title
                print(f'Active worksheet set to: {selected_title}')
                input('\nPress ENTER to return to menu...')
            except Exception as e:
                print('Failed to select worksheet:', e)
        elif choice == '3':
            print('\033[2J\033[H', end='', flush=True)
            cfg = _gs_config_global or {}
            if not cfg.get("creds") or not cfg.get("spreadsheet"):
                print('Google Sheets config missing. Set GS_CREDS and GS_SHEET (and GS_WORKSHEET).')
                continue

            try:
                import gspread
                from google.oauth2.service_account import Credentials

                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]
                creds = Credentials.from_service_account_file(cfg["creds"], scopes=scopes)
                client = gspread.authorize(creds)
                sh = client.open_by_key(cfg["spreadsheet"])
                active_worksheet = cfg.get("worksheet")
                worksheets = sh.worksheets()

                print("Delete Worksheet:")
                for idx, ws in enumerate(worksheets, start=1):
                    marker = "*" if ws.title == active_worksheet else " "
                    print(f' {idx}. {marker} {ws.title}')

                selection = input(
                    'Select worksheet to delete by number or exact name (Enter to cancel): '
                ).strip()
                if not selection:
                    continue

                selected_ws = None
                if selection.isdigit():
                    selected_index = int(selection)
                    if 1 <= selected_index <= len(worksheets):
                        selected_ws = worksheets[selected_index - 1]
                if selected_ws is None:
                    for ws in worksheets:
                        if ws.title == selection:
                            selected_ws = ws
                            break

                if not selected_ws:
                    print('Invalid selection.')
                    continue

                confirm = input(f'Delete worksheet "{selected_ws.title}"? (yes/no): ').strip().lower()
                if confirm == 'yes':
                    sh.del_worksheet(selected_ws)
                    print(f'Worksheet "{selected_ws.title}" deleted.')
                    if selected_ws.title == active_worksheet:
                        _gs_config_global["worksheet"] = None
                        print('Active worksheet was deleted. Reset to default.')
                else:
                    print('Deletion canceled.')
                input('\nPress ENTER to return to menu...')
            except Exception as e:
                print('Failed to delete worksheet:', e)
        elif choice == '4':
            print('\033[2J\033[H', end='', flush=True)
            cfg = _gs_config_global or {}
            if not cfg.get("creds") or not cfg.get("spreadsheet"):
                print('Google Sheets config missing. Set GS_CREDS and GS_SHEET (and GS_WORKSHEET).')
                continue

            try:
                import gspread
                from google.oauth2.service_account import Credentials

                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]
                creds = Credentials.from_service_account_file(cfg["creds"], scopes=scopes)
                client = gspread.authorize(creds)
                sh = client.open_by_key(cfg["spreadsheet"])
                active_worksheet = cfg.get("worksheet")
                worksheets = sh.worksheets()

                print("Rename Worksheet:")
                for idx, ws in enumerate(worksheets, start=1):
                    marker = "*" if ws.title == active_worksheet else " "
                    print(f' {idx}. {marker} {ws.title}')

                selection = input(
                    'Select worksheet to rename by number or exact name (Enter to cancel): '
                ).strip()
                if not selection:
                    continue

                selected_ws = None
                if selection.isdigit():
                    selected_index = int(selection)
                    if 1 <= selected_index <= len(worksheets):
                        selected_ws = worksheets[selected_index - 1]
                if selected_ws is None:
                    for ws in worksheets:
                        if ws.title == selection:
                            selected_ws = ws
                            break

                if not selected_ws:
                    print('Invalid selection.')
                    continue

                new_name = input(f'Enter new name for "{selected_ws.title}": ').strip()
                if not new_name:
                    print('Rename canceled.')
                    continue

                selected_ws.update_title(new_name)
                print(f'Worksheet renamed to "{new_name}".')
                if selected_ws.title == active_worksheet:
                    _gs_config_global["worksheet"] = new_name
                input('\nPress ENTER to return to menu...')
            except Exception as e:
                print('Failed to rename worksheet:', e)
        else:
            print('Invalid choice — enter 1-9.')

if __name__ == "__main__":
    main()
