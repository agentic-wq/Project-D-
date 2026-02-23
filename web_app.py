import os
import random
from datetime import datetime

import gspread
import streamlit as st
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

from app import fetch_related_items


load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _init_state() -> None:
    defaults = {
        "active_worksheet": os.getenv("GS_WORKSHEET", ""),
        "sheet_title": "",
        "sheet_key": os.getenv("GS_SHEET", ""),
        "quiz_stage": "idle",
        "quiz_items": [],
        "practice_index": 0,
        "quiz_remaining": {},
        "quiz_required": {},
        "quiz_streaks": {},
        "quiz_incorrect_streak": 0,
        "quiz_current_key": None,
        "quiz_message": "",
        "final_keys": [],
        "final_index": 0,
        "final_incorrect_streak": 0,
        "final_message": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _get_client() -> gspread.Client:
    creds_path = os.getenv("GS_CREDS", "")
    if not creds_path:
        raise RuntimeError("GS_CREDS is not set.")
    if not os.path.exists(creds_path):
        raise RuntimeError(f"GS_CREDS path does not exist: {creds_path}")
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_spreadsheet():
    sheet_key = st.session_state.get("sheet_key") or os.getenv("GS_SHEET", "")
    if not sheet_key:
        raise RuntimeError("GS_SHEET is not set.")
    client = _get_client()
    spreadsheet = client.open_by_key(sheet_key)
    st.session_state["sheet_title"] = spreadsheet.title
    st.session_state["sheet_key"] = sheet_key
    return spreadsheet


def _list_worksheets(spreadsheet):
    return spreadsheet.worksheets()


def _ensure_active_worksheet(spreadsheet):
    worksheets = _list_worksheets(spreadsheet)
    if not worksheets:
        ws = spreadsheet.add_worksheet(title="Sheet1", rows=100, cols=26)
        st.session_state["active_worksheet"] = ws.title
        return ws

    active_name = st.session_state.get("active_worksheet")
    if active_name:
        for ws in worksheets:
            if ws.title == active_name:
                return ws

    ws = worksheets[0]
    st.session_state["active_worksheet"] = ws.title
    return ws


def _read_abc(ws) -> dict:
    rows = ws.get_all_values()
    abc = {chr(ord("A") + i): "" for i in range(26)}
    for row in rows:
        if len(row) >= 2 and row[0].strip():
            key = row[0].strip()
            if key.casefold() == "key" and row[1].strip().casefold() == "value":
                continue
            abc[key] = row[1]
    return abc


def _save_abc(ws, abc: dict) -> None:
    rows = [[chr(ord("A") + i), str(abc.get(chr(ord("A") + i), ""))] for i in range(26)]
    ws.clear()
    ws.update(values=rows, range_name="A1")


def _ensure_quiz_results_ws(spreadsheet):
    try:
        return spreadsheet.worksheet("Quiz Results")
    except Exception:
        ws = spreadsheet.add_worksheet(title="Quiz Results", rows=1000, cols=3)
        ws.update(values=[["Timestamp", "Worksheet", "Status"]], range_name="A1")
        return ws


def _save_quiz_result(spreadsheet, worksheet_name: str, status: str = "Completed") -> None:
    results_ws = _ensure_quiz_results_ws(spreadsheet)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results_ws.append_row([timestamp, worksheet_name, status])


def _get_results_rows(spreadsheet):
    ws = _ensure_quiz_results_ws(spreadsheet)
    rows = ws.get_all_values()
    if not rows:
        return []
    headers = rows[0]
    entries = []
    for row in rows[1:]:
        if len(row) < 3:
            continue
        entries.append(
            {
                headers[0] if len(headers) > 0 else "Timestamp": row[0],
                headers[1] if len(headers) > 1 else "Worksheet": row[1],
                headers[2] if len(headers) > 2 else "Status": row[2],
            }
        )
    entries.reverse()
    return entries


def _render_sidebar(spreadsheet, ws) -> str:
    st.sidebar.title("Project D Web UI")
    st.sidebar.write(f"**Active Google Sheet:** :orange[{spreadsheet.title}]")
    st.sidebar.write(f"**Active Worksheet:** :orange[{ws.title}]")
    return st.sidebar.radio(
        "Navigate",
        [
            "Worksheet Management",
            "Create ABC",
            "Read ABC",
            "Update ABC",
            "Delete ABC",
            "Quiz",
            "Quiz Results",
        ],
    )


def _page_worksheet_management(spreadsheet, ws):
    st.header("Worksheet Management")
    worksheets = _list_worksheets(spreadsheet)
    names = [w.title for w in worksheets]

    st.subheader("List Worksheets")
    st.write(names)

    st.subheader("Select Worksheet")
    selected = st.selectbox("Choose worksheet", options=names, index=names.index(ws.title) if ws.title in names else 0)
    if st.button("Set Active Worksheet"):
        st.session_state["active_worksheet"] = selected
        st.success(f"Active worksheet set to {selected}.")
        st.rerun()

    st.subheader("Rename Worksheet")
    rename_from = st.selectbox("Worksheet to rename", options=names, key="rename_from")
    new_name = st.text_input("New worksheet name")
    if st.button("Rename Worksheet"):
        if not new_name.strip():
            st.warning("Please enter a new worksheet name.")
        else:
            target = spreadsheet.worksheet(rename_from)
            target.update_title(new_name.strip())
            if st.session_state.get("active_worksheet") == rename_from:
                st.session_state["active_worksheet"] = new_name.strip()
            st.success(f"Renamed {rename_from} to {new_name.strip()}.")
            st.rerun()

    st.subheader("Delete Worksheet")
    deletable_names = [name for name in names if len(names) > 1]
    if deletable_names:
        delete_target = st.selectbox("Worksheet to delete", options=deletable_names)
        confirm_delete = st.checkbox("I understand this will permanently delete the worksheet")
        if st.button("Delete Worksheet"):
            if not confirm_delete:
                st.warning("Please confirm deletion first.")
            else:
                target = spreadsheet.worksheet(delete_target)
                spreadsheet.del_worksheet(target)
                if st.session_state.get("active_worksheet") == delete_target:
                    first_ws = _list_worksheets(spreadsheet)[0]
                    st.session_state["active_worksheet"] = first_ws.title
                st.success(f"Deleted worksheet {delete_target}.")
                st.rerun()
    else:
        st.info("At least one worksheet must remain.")


def _page_create_abc(spreadsheet, ws):
    st.header("Create ABC")
    st.write("Generate A–Z values from Google Maps place search.")
    query = st.text_input("Search query", placeholder="e.g., coffee shops in Cork")
    limit = st.slider("Max places to fetch", min_value=5, max_value=40, value=20)

    if st.button("Fetch and Populate A–Z"):
        if not query.strip():
            st.warning("Enter a search query first.")
            return
        with st.spinner("Fetching places from Google Maps..."):
            items = fetch_related_items(query.strip(), limit=limit)

        if not items:
            st.warning("No places found.")
            return

        grouped = {chr(ord("A") + i): "" for i in range(26)}
        for name in items:
            first = name.strip()[:1].upper()
            if first in grouped:
                grouped[first] = f"{grouped[first]}, {name}".strip(", ") if grouped[first] else name

        _save_abc(ws, grouped)
        st.success(f"Saved {len(items)} place(s) into worksheet {ws.title}.")


def _page_read_abc(ws):
    st.header("Read ABC")
    abc = _read_abc(ws)
    rows = [{"Key": key, "Value": value} for key, value in abc.items()]
    st.table(rows)


def _page_update_abc(ws):
    st.header("Update ABC")
    abc = _read_abc(ws)
    keys = list(abc.keys())
    key = st.selectbox("Select key", options=keys)
    value = st.text_area("Value", value=str(abc.get(key, "")), height=120)
    if st.button("Save Value"):
        abc[key] = value
        _save_abc(ws, abc)
        st.success(f"Saved value for key {key}.")


def _page_delete_abc(ws):
    st.header("Delete ABC Values")
    abc = _read_abc(ws)
    populated_keys = [k for k, v in abc.items() if str(v).strip()]
    if not populated_keys:
        st.info("No populated values to delete.")
        return

    selected_keys = st.multiselect("Select key(s) to clear", options=populated_keys)
    if st.button("Clear Selected Values"):
        if not selected_keys:
            st.warning("Select at least one key.")
            return
        for key in selected_keys:
            abc[key] = ""
        _save_abc(ws, abc)
        st.success(f"Cleared values for: {', '.join(selected_keys)}")


def _reset_quiz_state():
    st.session_state["quiz_stage"] = "idle"
    st.session_state["quiz_items"] = []
    st.session_state["practice_index"] = 0
    st.session_state["quiz_remaining"] = {}
    st.session_state["quiz_required"] = {}
    st.session_state["quiz_streaks"] = {}
    st.session_state["quiz_incorrect_streak"] = 0
    st.session_state["quiz_current_key"] = None
    st.session_state["quiz_message"] = ""
    st.session_state["final_keys"] = []
    st.session_state["final_index"] = 0
    st.session_state["final_incorrect_streak"] = 0
    st.session_state["final_message"] = ""


def _start_quiz(ws):
    abc = _read_abc(ws)
    items = [(k, v) for k, v in abc.items() if str(v).strip()]
    if not items:
        return False

    st.session_state["quiz_items"] = sorted(items, key=lambda x: x[0].casefold())
    st.session_state["practice_index"] = 0
    st.session_state["quiz_stage"] = "practice"
    st.session_state["quiz_remaining"] = {k: v for k, v in items}
    st.session_state["quiz_required"] = {k: 1 for k, _ in items}
    st.session_state["quiz_streaks"] = {k: 0 for k, _ in items}
    st.session_state["quiz_incorrect_streak"] = 0
    st.session_state["quiz_current_key"] = None
    st.session_state["quiz_message"] = ""
    st.session_state["final_keys"] = sorted([k for k, _ in items], key=lambda x: x.casefold())
    st.session_state["final_index"] = 0
    st.session_state["final_incorrect_streak"] = 0
    st.session_state["final_message"] = ""
    return True


def _page_quiz(spreadsheet, ws):
    st.header("Quiz")

    cols = st.columns([1, 1])
    with cols[0]:
        if st.button("Start / Restart Quiz"):
            ok = _start_quiz(ws)
            if not ok:
                st.warning("No quiz questions available. Add data first.")
            st.rerun()
    with cols[1]:
        if st.button("Reset Quiz State"):
            _reset_quiz_state()
            st.rerun()

    stage = st.session_state.get("quiz_stage", "idle")

    if stage == "idle":
        st.info("Click 'Start / Restart Quiz' to begin.")
        return

    if stage == "practice":
        st.markdown("### :blue[Practice Mode]")
        items = st.session_state["quiz_items"]
        idx = st.session_state["practice_index"]
        key, value = items[idx]
        st.write(f"Practice {idx + 1}/{len(items)}")
        st.write(f"**Key:** {key}")
        st.write(f"**Value:** :orange[{value}]")

        if idx < len(items) - 1:
            if st.button("Next Practice Item"):
                st.session_state["practice_index"] = idx + 1
                st.rerun()
        else:
            if st.button("Start Quiz"):
                st.session_state["quiz_stage"] = "quiz"
                st.rerun()
        return

    if stage == "quiz":
        st.markdown("### :blue[Quiz]")
        remaining = st.session_state["quiz_remaining"]
        if not remaining:
            st.session_state["quiz_stage"] = "final"
            st.rerun()

        if st.session_state.get("quiz_current_key") not in remaining:
            st.session_state["quiz_current_key"] = random.choice(list(remaining.keys()))

        question_key = st.session_state["quiz_current_key"]
        expected = str(remaining[question_key]).strip()
        required = st.session_state["quiz_required"][question_key]
        streak = st.session_state["quiz_streaks"][question_key]

        st.write(f"Question key: **{question_key}**")
        st.write(f"Progress for this key: {streak + 1}/{required}")

        with st.form("quiz_form", clear_on_submit=True):
            answer = st.text_input("Enter value")
            submitted = st.form_submit_button("Submit Answer")

        if submitted:
            if answer.strip().casefold() == expected.casefold():
                streak += 1
                st.session_state["quiz_streaks"][question_key] = streak
                st.session_state["quiz_incorrect_streak"] = 0
                st.success(f"Correct! {len(remaining) - 1} key(s) remaining once this key is complete.")
            else:
                st.session_state["quiz_incorrect_streak"] += 1
                st.session_state["quiz_required"][question_key] = max(2, required * 2)
                st.session_state["quiz_streaks"][question_key] = 0
                st.error(f"Incorrect. Correct value is: {expected}")
                st.warning(
                    f'You must now answer "{question_key}" correctly '
                    f'{st.session_state["quiz_required"][question_key]} times in a row.'
                )
                if st.session_state["quiz_incorrect_streak"] >= 3:
                    st.info("Review:")
                    for k, v in st.session_state["quiz_items"]:
                        st.write(f"- {k}: {v}")
                    st.session_state["quiz_incorrect_streak"] = 0

            if (
                question_key in st.session_state["quiz_remaining"]
                and st.session_state["quiz_streaks"][question_key]
                >= st.session_state["quiz_required"][question_key]
            ):
                del st.session_state["quiz_remaining"][question_key]
                del st.session_state["quiz_required"][question_key]
                del st.session_state["quiz_streaks"][question_key]

            st.session_state["quiz_current_key"] = None
            st.rerun()
        return

    if stage == "final":
        st.markdown("### :blue[Final Quiz — Alphabetical Review]")
        final_keys = st.session_state["final_keys"]
        idx = st.session_state["final_index"]

        if idx >= len(final_keys):
            _save_quiz_result(spreadsheet, ws.title, "Completed")
            st.success("Congratulations! You have finished the quiz.")
            st.success("Your results have been saved and can be viewed in Quiz Results.")
            st.session_state["quiz_stage"] = "done"
            return

        current_key = final_keys[idx]
        abc_map = dict(st.session_state["quiz_items"])
        expected = str(abc_map[current_key]).strip()

        st.write(f"Final quiz {idx + 1}/{len(final_keys)}")
        st.write(f"**Key:** {current_key}")

        with st.form("final_form", clear_on_submit=True):
            answer = st.text_input("Enter value", key=f"final_answer_{idx}")
            submitted = st.form_submit_button("Submit Final Answer")

        if submitted:
            if answer.strip().casefold() == expected.casefold():
                st.success("Correct!")
                st.session_state["final_incorrect_streak"] = 0
                st.session_state["final_index"] = idx + 1
            else:
                st.error(f"Incorrect. Correct value is: {expected}")
                st.warning("Restarting final quiz from the beginning.")
                st.session_state["final_incorrect_streak"] += 1
                if st.session_state["final_incorrect_streak"] >= 3:
                    st.info("Review:")
                    for k, v in st.session_state["quiz_items"]:
                        st.write(f"- {k}: {v}")
                    st.session_state["final_incorrect_streak"] = 0
                st.session_state["final_index"] = 0
            st.rerun()
        return

    if stage == "done":
        st.success("Quiz completed. View your history in Quiz Results.")


def _page_quiz_results(spreadsheet):
    st.header("Quiz Results")
    rows = _get_results_rows(spreadsheet)
    if not rows:
        st.info("No quiz results yet.")
        return
    st.table(rows)


def main():
    st.set_page_config(page_title="Project D Web UI", page_icon="📘", layout="wide")
    _init_state()

    st.title("Project D")
    st.caption("Web front end for worksheet management, ABC workflows, quiz, and results")

    try:
        spreadsheet = _get_spreadsheet()
        ws = _ensure_active_worksheet(spreadsheet)
    except Exception as e:
        st.error(str(e))
        st.info("Set GS_CREDS and GS_SHEET in your .env file, then refresh.")
        return

    selected_page = _render_sidebar(spreadsheet, ws)

    if selected_page == "Worksheet Management":
        _page_worksheet_management(spreadsheet, ws)
    elif selected_page == "Create ABC":
        _page_create_abc(spreadsheet, ws)
    elif selected_page == "Read ABC":
        _page_read_abc(ws)
    elif selected_page == "Update ABC":
        _page_update_abc(ws)
    elif selected_page == "Delete ABC":
        _page_delete_abc(ws)
    elif selected_page == "Quiz":
        _page_quiz(spreadsheet, ws)
    elif selected_page == "Quiz Results":
        _page_quiz_results(spreadsheet)


if __name__ == "__main__":
    main()
