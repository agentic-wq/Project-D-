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
from dotenv import load_dotenv

from langgraph.graph import START, StateGraph
import os

# Global config for Google Sheets (workaround for state persistence)
_gs_config_global = None


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
    """
    global _gs_config_global
    #PRINT004 - print("--- in gs_load_node ---")
    #PRINT005 - print("state in gs_load_node:", state)
    cfg = _gs_config_global or {}
    #PRINT006 - print("Google Sheets config:", cfg)
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
        ws = sh.worksheet(cfg.get("worksheet", "Sheet1"))
        rows = ws.get_all_values()
        abc = dict(state.get("abc", {}))
        for row in rows:
            if not row:
                continue
            if len(row) >= 2 and row[0].strip():
                abc[row[0].strip()] = row[1]
        #PRINT007 - print("Loaded ABC from Google Sheet:", cfg.get("spreadsheet"))
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

    It will overwrite the worksheet with two columns: key, value (with header).
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
        ws = sh.worksheet(cfg.get("worksheet", "Sheet1"))
        abc = dict(state.get("abc", {}))
        rows = [["key", "value"]] + [[k, v] for k, v in abc.items()]
        ws.clear()
        ws.update(values=rows, range_name="A1")
        print("Saved ABC to Google Sheet:", cfg.get("spreadsheet"))
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
    args = parser.parse_args()
    
    # Check for command line args first, then fall back to environment variables
    gs_creds = args.gs_creds or os.getenv("GS_CREDS")
    gs_sheet = args.gs_sheet or os.getenv("GS_SHEET")
    gs_worksheet = args.gs_worksheet or os.getenv("GS_WORKSHEET", "Sheet1")
    #PRINT014 - print(f"gs_creds path: {gs_creds}, gs_sheet ID: {gs_sheet}, gs_worksheet name: {gs_worksheet}") 
    
    if gs_creds and gs_sheet:
        _gs_config_global = {
            "creds": gs_creds,
            "spreadsheet": gs_sheet,
            "worksheet": gs_worksheet,
        }
    #PRINT017 -print("_gs_config_global:", _gs_config_global)

    # Define table display function
    def _print_fixed_keys_values(d: dict, fixed_keys: list[str], cols: int = 4) -> None:
        # Create cells containing values only, in order of fixed_keys
        cells = [str(d.get(k, "")) for k in fixed_keys]
        if not cells:
            print("\n-- ABC store --\n(empty)")
            return
        rows = (len(cells) + cols - 1) // cols
        # pad to full grid
        padded = cells + [""] * (rows * cols - len(cells))
        col_width = max(len(c) for c in padded + [" "])
        sep_piece = "+-" + ("-" * col_width) + "-"
        sep = sep_piece * cols + "+"
        print()
        print("-- ABC store --")
        print(sep)
        for r in range(rows):
            row_cells = padded[r * cols:(r + 1) * cols]
            row_line = ""
            for c in row_cells:
                row_line += f"| {c.ljust(col_width)} "
            row_line += "|"
            print(row_line)
            print(sep)

    # Interactive prompt handled in main (always interactive)
    interactive_pairs = {}
    fixed_keys = [chr(ord('A') + i) for i in range(26)]
    while True:
        print('\nMenu:')
        print('1. View ABC')
        print('2. Edit ABC')
        print('3. Quiz')
        try:
            choice = input('Choose option (1/2/3): ').strip()
        except EOFError:
            break
        if not choice:
            print('Please choose option 1, 2, or 3.')
            continue
        if choice == '1':
            #View ABC - load from Google Sheets and display as table
            temp_state = {"abc": {}}
            if interactive_pairs:
                temp_state['to_set'] = interactive_pairs
            graph = build_graph()
            compiled = graph.compile()
            result = compiled.invoke(temp_state)
            _print_fixed_keys_values(result.get("abc", {}), fixed_keys, cols=4)
        elif choice == '2':
            #Edit ABC
            while True:
                try:
                    key = input('Key to set (blank to finish): ').strip()
                except EOFError:
                    break
                if not key:
                    break
                try:
                    val = input(f'Value for "{key}": ').strip()
                except EOFError:
                    val = ""
                interactive_pairs[key] = val
        elif choice == '3':
            #Quiz
            temp_abc = {}
            if interactive_pairs:
                temp_abc.update(interactive_pairs)
            print('\n-- Current ABC --')
            if not temp_abc:
                print('(empty)')
            else:
                for k, v in temp_abc.items():
                    print(f'{k}: {v}')
        else:
            print('Invalid choice — enter 1, 2, or 3.')

    # build base state and merge any interactive pairs so graph nodes see them
    base_state = {"abc": {}}
    if interactive_pairs:
        base_state['to_set'] = interactive_pairs

    graph = build_graph()
    compiled = graph.compile()
    result = compiled.invoke(base_state)


if __name__ == "__main__":
    main()
