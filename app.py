"""Simple LangGraph CLI that preloads key/value pairs into the graph state.

Run:
  pip install -r requirements.txt
  python app.py              # prints the preloaded kv store
  python app.py --set color blue  # sets a key then prints the store

This example uses a StateGraph with a small "kv" dict stored in state.
"""
from typing import Dict
from typing_extensions import TypedDict
import argparse

from langgraph.graph import START, StateGraph
import os

# Global config for Google Sheets (workaround for state persistence)
_gs_config_global = None
_no_interactive_global = False


class State(TypedDict):
    kv: Dict[str, str]
    # optional helper key used only when invoking set via CLI
    to_set: Dict[str, str]


def set_kv(state: State) -> dict:
    """If `to_set` present, merge it into `kv` and return updated state."""
    print("--- in set_kv node ---" )
    kv = dict(state.get("kv", {}))
    to_set = state.get("to_set") or {}
    if to_set:
        kv.update(to_set)
    return {
        "kv": kv,
        "_gs_config": state.get("_gs_config"),
        "_no_interactive": state.get("_no_interactive"),
    }


def show_kv(state: State) -> dict:
    """Return state without changes (we'll print result after invoke)."""
    print("--- in show_kv node ---")
    return {
        "kv": state.get("kv", {}),
        "_gs_config": state.get("_gs_config"),
        "_no_interactive": state.get("_no_interactive"),
    }


def interactive_set(state: State) -> dict:
    """No-op placeholder — interactive input is handled in `main()`."""
    print("--- in interactive_set node ---")
    return dict(state)


def gs_load_node(state: State) -> dict:
    """Load key/value pairs from a Google Sheets worksheet into `kv`.

    Expects `_gs_config` in state with keys: `creds` (path to service account
    JSON) and `spreadsheet` (spreadsheet ID), optional `worksheet`.
    """
    global _gs_config_global
    print("--- in gs_load_node ---")
    print("state in gs_load_node:", state)
    cfg = _gs_config_global or {}
    print("Google Sheets config:", cfg)
    if not cfg.get("creds") or not cfg.get("spreadsheet"):
        return {
            "kv": state.get("kv", {}),
            "_gs_config": state.get("_gs_config"),
            "_no_interactive": state.get("_no_interactive"),
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
        kv = dict(state.get("kv", {}))
        for row in rows:
            if not row:
                continue
            if len(row) >= 2 and row[0].strip():
                kv[row[0].strip()] = row[1]
        print("Loaded KV from Google Sheet:", cfg.get("spreadsheet"))
        return {
            "kv": kv,
            "_gs_config": state.get("_gs_config"),
            "_no_interactive": state.get("_no_interactive"),
        }
    except Exception as e:
        print("Warning: failed to load from Google Sheets:", e)
        return {
            "kv": state.get("kv", {}),
            "_gs_config": state.get("_gs_config"),
            "_no_interactive": state.get("_no_interactive"),
        }


def gs_save_node(state: State) -> dict:
    """Save the `kv` dict into the configured Google Sheets worksheet.

    It will overwrite the worksheet with two columns: key, value (with header).
    Requires `_gs_config` in state.
    """
    global _gs_config_global
    print("--- in gs_save_node ---")
    print("state in gs_save_node:", state)
    cfg = _gs_config_global or {}
    if not cfg.get("creds") or not cfg.get("spreadsheet"):
        print("No Google Sheets config provided; skipping save.")
        return {

            "kv": state.get("kv", {}),
            "_gs_config": state.get("_gs_config"),
            "_no_interactive": state.get("_no_interactive"),
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
        kv = dict(state.get("kv", {}))
        rows = [["key", "value"]] + [[k, v] for k, v in kv.items()]
        ws.clear()
        ws.update("A1", rows)
        print("Saved KV to Google Sheet:", cfg.get("spreadsheet"))
        return {
            "kv": kv,
            "_gs_config": state.get("_gs_config"),
            "_no_interactive": state.get("_no_interactive"),
        }
    except Exception as e:
        import traceback
        print("Warning: failed to save to Google Sheets:", e)
        print("Traceback:", traceback.format_exc())
        return {
            "kv": state.get("kv", {}),
            "_gs_config": state.get("_gs_config"),
            "_no_interactive": state.get("_no_interactive"),
        }


def build_graph() -> StateGraph:
    print("--- building graph ---")
    #print("state in build_graph:", State)
    graph = StateGraph(State)
    print("graph created", graph)
    # nodes
    graph.add_node("gs_load", gs_load_node)
    #print("state after gs_load_node:", State)
    graph.add_node("set_kv", set_kv)
    graph.add_node("gs_save", gs_save_node)
    graph.add_node("show_kv", show_kv)

    # linear flow: START -> gs_load -> set_kv -> gs_save -> show_kv
    graph.add_edge(START, "gs_load")
    graph.add_edge("gs_load", "set_kv")
    graph.add_edge("set_kv", "gs_save")
    graph.add_edge("gs_save", "show_kv")
    return graph


def main():
    global _gs_config_global, _no_interactive_global
    print("--- starting main ")
    parser = argparse.ArgumentParser(description="LangGraph KV starter app")
    parser.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"),
                        help="set a key/value pair before running the graph")
    parser.add_argument("--gs-creds", help="path to Google service account JSON credentials")
    parser.add_argument("--gs-sheet", help="Google Sheets spreadsheet ID to load/save")
    parser.add_argument("--gs-worksheet", help="worksheet name (default: Sheet1)")
    parser.add_argument("--no-interactive", action="store_true", help="skip interactive prompts")
    args = parser.parse_args()

    initial_kv = {"name": "Alice", "role": "developer", "project": "Project D"}
    initial_state: State = {"kv": initial_kv}
    print("Initial State Definition:", initial_state)

    if args.set:
        k, v = args.set
        initial_state["to_set"] = {k: v}
        print("Initial State,'to_set:'", initial_state)

    # Google Sheets configuration (optional) — store in global
    if args.gs_creds and args.gs_sheet:
        _gs_config_global = {
            "creds": args.gs_creds,
            "spreadsheet": args.gs_sheet,
            "worksheet": args.gs_worksheet or "Sheet1",
        }
        print("_gs_config_global:", _gs_config_global)

    # Interactive prompt handled in main (so LangGraph execution stays non-blocking)
    if not args.no_interactive:
        print('\n-- interactive set: add key:value pairs (blank to finish) --')
        interactive_pairs = {}
        while True:
            try:
                entry = input('Add key:value: ').strip()
            except EOFError:
                break
            if not entry:
                break
            if ':' not in entry:
                print('Invalid format — use key:value')
                continue
            key, val = entry.split(':', 1)
            interactive_pairs[key.strip()] = val.strip()
            print(f'Added: {key.strip()} = {val.strip()}')
        if interactive_pairs:
            existing = initial_state.get('to_set', {})
            existing.update(interactive_pairs)
            initial_state['to_set'] = existing
            print("Initial State,'to_set:'", initial_state)

    if args.no_interactive:
        _no_interactive_global = True
        initial_state["_no_interactive"] = True
        print("Initial State,'_no_interactive:'", initial_state)

    graph = build_graph()
    compiled = graph.compile()
    print("Graph compiled, invoking with initial state:", initial_state)
    result = compiled.invoke(initial_state)

    print("*** final KV store ***")
    for kk, vv in result["kv"].items():
        print(f"{kk}: {vv}")


if __name__ == "__main__":
    main()
