import os
import random
import time
from datetime import datetime

import gspread
import streamlit as st
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

from app import fetch_related_items, fetch_related_items_agentic


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
        "quiz_review_timer": None,
        "quiz_submitted_values": {},
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


@st.cache_resource
def _get_spreadsheet_cached(sheet_key: str):
    if not sheet_key:
        raise RuntimeError("GS_SHEET is not set.")
    client = _get_client()
    spreadsheet = client.open_by_key(sheet_key)
    return spreadsheet


def _get_spreadsheet():
    sheet_key = st.session_state.get("sheet_key") or os.getenv("GS_SHEET", "")
    if not sheet_key:
        raise RuntimeError("GS_SHEET is not set.")
    spreadsheet = _get_spreadsheet_cached(sheet_key)
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
    abc = {chr(ord("A") + i): [] for i in range(26)}
    for row in rows:
        if not row or not row[0].strip():
            continue
        key = row[0].strip()
        if key.casefold() == "key":
            continue
        if key in abc:
            values = [v.strip() for v in row[1:] if v.strip()]
            abc[key] = values
    return abc


def _save_abc(ws, abc: dict) -> None:
    rows = []
    max_cols = max((len(vals) for vals in abc.values()), default=0) + 1
    for i in range(26):
        key = chr(ord("A") + i)
        row = [key] + [str(v) for v in abc.get(key, [])]
        row += [""] * (max_cols - len(row))
        rows.append(row)
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
    st.sidebar.write(f"**Active Google Sheet:** :orange[{spreadsheet.title}]")
    st.sidebar.write(f"**Active Worksheet:** :orange[{ws.title}]")
    return st.sidebar.radio(
        "Navigate",
        [
            "Worksheet",
            "ABC",
            "Quiz",
        ],
    )


def _page_worksheet_management(spreadsheet, ws):
    st.header("Worksheet")
    worksheets = _list_worksheets(spreadsheet)
    names = [w.title for w in worksheets]
    list_tab, select_tab, rename_tab, delete_tab = st.tabs(
        ["List", "Select", "Rename", "Delete"]
    )

    with list_tab:
        st.subheader("List Worksheets")
        st.write(names)

    with select_tab:
        st.subheader("Select Worksheet")
        selected = st.selectbox("Choose worksheet", options=names, index=names.index(ws.title) if ws.title in names else 0, key="select_worksheet_select")
        if st.button("Set Active Worksheet", key="select_worksheet_button"):
            st.session_state["active_worksheet"] = selected
            st.success(f"Active worksheet set to {selected}.")
            st.rerun()

    with rename_tab:
        st.subheader("Rename Worksheet")
        rename_from = st.selectbox("Worksheet to rename", options=names, key="rename_from")
        new_name = st.text_input("New worksheet name", key="rename_new_name")
        if st.button("Rename Worksheet", key="rename_worksheet_button"):
            if not new_name.strip():
                st.warning("Please enter a new worksheet name.")
            else:
                target = spreadsheet.worksheet(rename_from)
                target.update_title(new_name.strip())
                if st.session_state.get("active_worksheet") == rename_from:
                    st.session_state["active_worksheet"] = new_name.strip()
                st.success(f"Renamed {rename_from} to {new_name.strip()}.")
                st.rerun()

    with delete_tab:
        st.subheader("Delete Worksheet")
        deletable_names = [name for name in names if len(names) > 1]
        if deletable_names:
            delete_target = st.selectbox("Worksheet to delete", options=deletable_names, key="delete_worksheet_select")
            confirm_delete = st.checkbox("I understand this will permanently delete the worksheet", key="delete_worksheet_confirm")
            if st.button("Delete Worksheet", key="delete_worksheet_button"):
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


def _page_generate_abc_custom(ws):
    """Allow user to manually enter custom A–Z values."""
    st.subheader("📝 Custom Entry")
    st.write("Manually enter values for each key.")
    
    key = st.selectbox("Select key", options=[chr(ord("A") + i) for i in range(26)], key="custom_select_key")
    value = st.text_input(f"Enter value for {key}", placeholder="e.g., Apple", key="custom_input_value")
    
    if st.button("Add Value", key="custom_add_button"):
        if not value.strip():
            st.warning("Please enter a value.")
            return
        
        abc = _read_abc(ws)
        if value.strip() not in abc.get(key, []):
            abc[key].append(value.strip())
            _save_abc(ws, abc)
            st.success(f"Added '{value.strip()}' to key {key}.")
            st.rerun()
        else:
            st.warning(f"'{value.strip()}' is already in key {key}.")


def _page_generate_abc_google_maps(ws):
    """Fetch places from Google Maps."""
    st.subheader("📍 Google Maps Search")
    st.write("Generate A–Z values from real Google Maps locations.")
    
    query = st.text_input("Search query", placeholder="e.g., coffee shops in Cork", key="maps_search_query")
    limit = st.slider("Max places to fetch", min_value=5, max_value=40, value=20)

    if st.button("Fetch and Populate A–Z", key="maps_fetch_button"):
        if not query.strip():
            st.warning("Enter a search query first.")
            return
        with st.spinner("Fetching places from Google Maps..."):
            items = fetch_related_items(query.strip(), limit=limit)

        if not items:
            st.warning("No places found.")
            return

        grouped = {chr(ord("A") + i): [] for i in range(26)}
        for name in items:
            first = name.strip()[:1].upper()
            if first in grouped:
                grouped[first].append(name.strip())

        _save_abc(ws, grouped)
        st.success(f"Saved {len(items)} place(s) into worksheet {ws.title}.")


def _page_generate_abc_agentic(ws):
    """Generate values using AI agent."""
    st.subheader("🤖 AI Agent Generation")
    st.write("Generate A–Z values using an AI agent powered by LangGraph and LLMs.")
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        st.warning("⚠️ **OPENAI_API_KEY not configured**")
        st.info("To use AI generation, set the OPENAI_API_KEY environment variable in your .env file:")
        st.code("OPENAI_API_KEY=sk-...", language="bash")
        st.write("Get your API key from [OpenAI Platform](https://platform.openai.com/account/api-keys)")
        return
    
    st.success("✅ OpenAI API key detected. Ready to generate!")
    
    category = st.text_input(
        "Category",
        placeholder="e.g., Animals, Foods, Countries, Historical Figures",
        help="The theme or category for generating A–Z examples",
        key="agentic_category"
    )
    limit = st.slider(
        "Max items per key",
        min_value=1,
        max_value=10,
        value=3,
        help="Number of examples to generate for each A–Z letter",
        key="agentic_limit"
    )
    
    if st.button("🚀 Generate with AI Agent", key="agentic_generate_button"):
        if not category.strip():
            st.warning("Please enter a category.")
            return
        
        with st.spinner(f"🤖 Generating '{category}' examples for A–Z... (this may take 30-60 seconds)"):
            try:
                generated = fetch_related_items_agentic(category.strip(), limit=limit)
                
                # Count total items generated
                total_items = sum(len(items) for items in generated.values())
                
                if total_items == 0:
                    st.warning("No items were generated. Please check your OpenAI API key and try again.")
                    return
                
                # Save to worksheet
                _save_abc(ws, generated)
                st.success(f"✅ Generated {total_items} items across A–Z!")
                
                # Show preview
                st.subheader("Preview of Generated Items")
                preview_data = []
                for key in sorted(generated.keys()):
                    items = generated[key]
                    if items:
                        preview_data.append({"Key": key, "Items": ", ".join(items)})
                
                if preview_data:
                    import pandas as pd
                    df = pd.DataFrame(preview_data)
                    st.dataframe(df, hide_index=True, width='stretch')
                
            except Exception as e:
                st.error(f"❌ Error during generation: {str(e)}")
                st.info("Please ensure:")
                st.write("- OPENAI_API_KEY is set in your .env file")
                st.write("- Your OpenAI account has available credits")
                st.write("- Your API key is valid and not expired")


def _page_generate_abc(spreadsheet, ws):
    st.header("Generate ABC")
    st.write("Choose how you want to populate your A–Z values.")
    
    # Worksheet selection/creation
    st.subheader("1️⃣ Select or Create Worksheet")
    worksheets = _list_worksheets(spreadsheet)
    worksheet_names = [w.title for w in worksheets]
    
    create_new = st.checkbox("Create a new worksheet", key="generate_create_new_ws")
    
    if create_new:
        new_ws_name = st.text_input(
            "New worksheet name",
            placeholder="e.g., Animals, Foods, Countries",
            key="generate_new_ws_name"
        )
        if st.button("Create Worksheet", key="generate_create_ws_button"):
            if not new_ws_name.strip():
                st.warning("Please enter a worksheet name.")
                return
            
            # Create new worksheet
            try:
                new_ws = spreadsheet.add_worksheet(title=new_ws_name.strip(), rows=100, cols=26)
                st.session_state["active_worksheet"] = new_ws_name.strip()
                ws = new_ws
                st.success(f"Created worksheet '{new_ws_name.strip()}'")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create worksheet: {str(e)}")
                return
    else:
        selected_ws = st.selectbox(
            "Use existing worksheet",
            options=worksheet_names,
            index=worksheet_names.index(ws.title) if ws.title in worksheet_names else 0,
            key="generate_select_ws"
        )
        if selected_ws != ws.title:
            ws = spreadsheet.worksheet(selected_ws)
            st.session_state["active_worksheet"] = selected_ws
    
    st.divider()
    
    # Data source selection
    st.subheader("2️⃣ Select Data Source")
    source = st.radio(
        "How would you like to populate your A–Z values?",
        options=["Custom Entry", "Google Maps", "AI Agent"],
        horizontal=True,
        key="generate_abc_source"
    )
    
    st.divider()
    
    if source == "Custom Entry":
        _page_generate_abc_custom(ws)
    elif source == "Google Maps":
        _page_generate_abc_google_maps(ws)
    elif source == "AI Agent":
        _page_generate_abc_agentic(ws)


def _page_read_abc(ws):
    st.header("Read ABC")
    abc = _read_abc(ws)
    import pandas as pd
    max_cols = max((len(vals) for vals in abc.values()), default=0)
    rows = []
    for key in sorted(abc.keys()):
        row = {"Key": key}
        values = abc.get(key, [])
        for i in range(max_cols):
            row[f"Value {i+1}"] = values[i] if i < len(values) else ""
        rows.append(row)
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True, height='content')


def _page_update_abc(ws):
    st.header("Update ABC")
    abc = _read_abc(ws)
    keys = list(abc.keys())
    key = st.selectbox("Select key", options=keys, key="update_select_key")
    current_values = abc.get(key, [])
    
    st.write(f"Current values for **{key}**:")
    for i, val in enumerate(current_values):
        col1, col2 = st.columns([1, 0.2])
        with col1:
            st.write(f"{i+1}. {val}")
    
    st.write("Add or update value:")
    new_value = st.text_input("New value", placeholder="Enter a value to add", key="update_new_value")
    if st.button("Add Value", key="update_add_button"):
        if new_value.strip():
            abc[key].append(new_value.strip())
            _save_abc(ws, abc)
            st.success(f"Added value to key {key}.")
            st.rerun()
    
    if current_values:
        st.write("Remove a value:")
        value_to_remove = st.selectbox("Select value to remove", options=current_values, key="update_remove_select")
        if st.button("Remove Value", key="update_remove_button"):
            abc[key].remove(value_to_remove)
            _save_abc(ws, abc)
            st.success(f"Removed value from key {key}.")
            st.rerun()


def _page_delete_abc(ws):
    st.header("Delete ABC Values")
    abc = _read_abc(ws)
    populated_keys = [k for k, v in abc.items() if v]
    if not populated_keys:
        st.info("No populated values to delete.")
        return

    key = st.selectbox("Select key to delete from", options=populated_keys, key="delete_key_select")
    values = abc.get(key, [])
    
    if not values:
        st.info(f"No values for key {key}.")
        return
    
    st.write(f"Values for key **{key}**:")
    for val in values:
        st.write(f"- {val}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear All Values for This Key", key="clear_all_button"):
            abc[key] = []
            _save_abc(ws, abc)
            st.success(f"Cleared all values for key {key}.")
            st.rerun()
    
    with col2:
        select_value = st.selectbox("Or select a single value to delete", options=values, key="delete_value_select")
        if st.button("Delete Selected Value", key="delete_value_button"):
            if select_value in abc[key]:
                abc[key].remove(select_value)
                _save_abc(ws, abc)
                st.success(f"Deleted value from key {key}.")
                st.rerun()


def _page_abc_management(spreadsheet, ws):
    st.header("ABC")
    generate_tab, read_tab, update_tab, delete_tab = st.tabs(
        ["Generate", "Read", "Update", "Delete"]
    )

    with generate_tab:
        _page_generate_abc(spreadsheet, ws)

    with read_tab:
        _page_read_abc(ws)

    with update_tab:
        _page_update_abc(ws)

    with delete_tab:
        _page_delete_abc(ws)


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
    st.session_state["quiz_mode"] = None
    st.session_state["should_save_results"] = False


def _start_quiz(ws):
    abc = _read_abc(ws)
    items = [(k, v) for k, v in abc.items() if v]
    if not items:
        return False

    # Flatten items so each value gets shown separately
    flattened = []
    for key, values in items:
        for val in values:
            flattened.append((key, val))
    
    st.session_state["quiz_items"] = sorted(flattened, key=lambda x: x[1].casefold())
    st.session_state["practice_index"] = 0
    st.session_state["quiz_stage"] = "stage_select"
    st.session_state["quiz_remaining"] = {i: (k, v) for i, (k, v) in enumerate(flattened)}
    st.session_state["quiz_required"] = {i: 1 for i, _ in enumerate(flattened)}
    st.session_state["quiz_streaks"] = {i: 0 for i, _ in enumerate(flattened)}
    st.session_state["quiz_incorrect_streak"] = 0
    st.session_state["quiz_current_key"] = None
    st.session_state["quiz_message"] = ""
    st.session_state["quiz_submitted_values"] = {k: [] for k, _ in items}
    st.session_state["final_keys"] = sorted(set(k for k, _ in flattened), key=lambda x: x.casefold())
    st.session_state["final_index"] = 0
    st.session_state["final_incorrect_streak"] = 0
    st.session_state["final_message"] = ""
    st.session_state["quiz_mode"] = None
    st.session_state["should_save_results"] = False
    return True


def _page_quiz(spreadsheet, ws):
    stage = st.session_state.get("quiz_stage", "idle")

    if stage == "idle":
        ok = _start_quiz(ws)
        if not ok:
            st.warning("No quiz questions available. Add data first.")
            return
        st.rerun()

    if stage == "stage_select":
        st.write("What would you like to do?")
        if st.button("Practice Only", key="stage_practice_only"):
            st.session_state["quiz_mode"] = "practice_only"
            st.session_state["should_save_results"] = False
            st.session_state["quiz_stage"] = "practice"
            st.rerun()
        if st.button("Quiz Only", key="stage_quiz_only"):
            st.session_state["quiz_mode"] = "quiz_only"
            st.session_state["should_save_results"] = True
            st.session_state["quiz_stage"] = "quiz"
            st.rerun()
        if st.button("Final Only", key="stage_final_only"):
            st.session_state["quiz_mode"] = "final_only"
            st.session_state["should_save_results"] = True
            st.session_state["quiz_stage"] = "final"
            st.rerun()
        if st.button("All 3 Stages", key="stage_all_stages"):
            st.session_state["quiz_mode"] = "all_stages"
            st.session_state["should_save_results"] = True
            st.session_state["quiz_stage"] = "practice"
            st.rerun()
        return

    if stage == "practice":
        st.markdown("### :orange[Practice Mode]")
        items = st.session_state["quiz_items"]
        idx = st.session_state["practice_index"]
        
        # Show 4 values at a time
        batch_size = 4
        batch_items = items[idx:idx + batch_size]
        
        # Display in a single column
        for _, value in batch_items:
            st.write(f"**{value}**")
        
        # Navigation
        if idx + batch_size < len(items):
            if st.button("Next", key="practice_next_button"):
                st.session_state["practice_index"] = idx + batch_size
                st.rerun()
        else:
            mode = st.session_state.get("quiz_mode", "all_stages")
            if mode == "practice_only":
                if st.button("Exit Practice", key="practice_exit_button"):
                    st.session_state["quiz_stage"] = "done"
                    st.rerun()
            else:
                if st.button("Start Quiz", key="practice_start_quiz_button"):
                    st.session_state["quiz_stage"] = "quiz"
                    st.rerun()
        return

    if stage == "quiz":
        st.markdown("### :orange[Quiz]")
        remaining = st.session_state["quiz_remaining"]
        if not remaining:
            st.session_state["quiz_stage"] = "final"
            st.rerun()

        if st.session_state.get("quiz_current_key") not in remaining:
            st.session_state["quiz_current_key"] = random.choice(list(remaining.keys()))

        question_idx = st.session_state["quiz_current_key"]
        question_key, _ = remaining[question_idx]
        required = st.session_state["quiz_required"][question_idx]
        streak = st.session_state["quiz_streaks"][question_idx]
        
        # Get all values for this key from quiz_items
        all_values_for_key = [v for k, v in st.session_state["quiz_items"] if k == question_key]
        submitted_values = st.session_state["quiz_submitted_values"].get(question_key, [])
        remaining_values = [v for v in all_values_for_key if not any(v.casefold() == sv.casefold() for sv in submitted_values)]
        
        st.write(f"**Key:** {question_key}")
        st.write(f"**Values to submit:** {len(remaining_values)}/{len(all_values_for_key)}")
        st.write("**Remaining values:**")
        for val in remaining_values:
            st.write(f"• {val}")

        # Check if review timer is active
        timer_active = False
        time_remaining = 0
        if st.session_state.get("quiz_review_timer"):
            time_remaining = st.session_state["quiz_review_timer"] - time.time()
            if time_remaining > 0:
                timer_active = True
            else:
                st.session_state["quiz_review_timer"] = None

        if timer_active:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.metric("Review Timer", f"{int(time_remaining)} sec")
            st.warning("Please review the material before continuing")
            with st.form("quiz_form", clear_on_submit=True):
                answer = st.text_input("Enter the value(s)", disabled=True, key="quiz_answer_timer")
                submitted = st.form_submit_button("Submit Answer", disabled=True)
            time.sleep(0.5)
            st.rerun()
        else:
            with st.form("quiz_form", clear_on_submit=True):
                answer = st.text_input("Enter the value(s)", key="quiz_answer")
                submitted = st.form_submit_button("Submit Answer")

        # Display any stored feedback from previous submission
        if st.session_state.get("quiz_feedback"):
            feedback = st.session_state["quiz_feedback"]
            if feedback.get("type") == "success":
                st.success(feedback.get("message"))
            elif feedback.get("type") == "error":
                st.error(feedback.get("message"))
            if feedback.get("warning"):
                st.warning(feedback.get("warning"))
            if feedback.get("review"):
                st.session_state["quiz_review_timer"] = time.time() + 45
                st.info("Review:")
                for item in feedback.get("review", []):
                    st.write(item)
            st.session_state["quiz_feedback"] = None

        if submitted:
            # User needs to type one of the values that correspond to this key
            question_key, _ = remaining[question_idx]
            all_values = remaining[question_idx][1] if isinstance(remaining[question_idx][1], list) else [remaining[question_idx][1]]
            submitted_values = st.session_state["quiz_submitted_values"].get(question_key, [])
            
            # Check if value is correct
            is_correct = any(answer.strip().casefold() == val.casefold() for val in all_values)
            
            # Check if value has already been submitted
            already_submitted = any(answer.strip().casefold() == val.casefold() for val in submitted_values)
            
            feedback = {}
            if not is_correct:
                st.session_state["quiz_incorrect_streak"] += 1
                st.session_state["quiz_required"][question_idx] = max(2, required * 2)
                st.session_state["quiz_streaks"][question_idx] = 0
                feedback["type"] = "error"
                feedback["message"] = f"Incorrect. Correct value(s): {'; '.join(all_values)}"
                feedback["warning"] = f'You must now answer correctly {st.session_state["quiz_required"][question_idx]} times in a row.'
                if st.session_state["quiz_incorrect_streak"] >= 3:
                    feedback["review"] = [f"- {k}: {v}" for idx, (k, v) in remaining.items()]
                    st.session_state["quiz_incorrect_streak"] = 0
            elif already_submitted:
                feedback["type"] = "error"
                feedback["message"] = f"You've already submitted '{answer}' for this key. Try a different value!"
            else:
                # Correct and not yet submitted
                streak += 1
                st.session_state["quiz_streaks"][question_idx] = streak
                st.session_state["quiz_incorrect_streak"] = 0
                
                # Track the submitted value
                submitted_values.append(answer.strip())
                st.session_state["quiz_submitted_values"][question_key] = submitted_values
                
                # Calculate progress
                values_completed = len(submitted_values)
                total_values = len(all_values)
                feedback["type"] = "success"
                feedback["message"] = f"Correct! Progress for '{question_key}': {values_completed}/{total_values}"

            st.session_state["quiz_feedback"] = feedback

            # Check if all values for this key have been submitted
            if is_correct and not already_submitted:
                submitted_values = st.session_state["quiz_submitted_values"][question_key]
                if len(submitted_values) >= len(all_values):
                    # All values for this key submitted, remove from quiz
                    del st.session_state["quiz_remaining"][question_idx]
                    del st.session_state["quiz_required"][question_idx]
                    del st.session_state["quiz_streaks"][question_idx]

            st.session_state["quiz_current_key"] = None
            st.rerun()
        
        # After quiz is complete, check if we should move to final or done
        if not remaining:
            mode = st.session_state.get("quiz_mode", "all_stages")
            if mode == "quiz_only":
                if st.session_state.get("should_save_results"):
                    _save_quiz_result(spreadsheet, ws.title, "Completed")
                st.success("Congratulations! You have completed the quiz.")
                st.success("Your results have been saved and can be viewed in Quiz Results.")
                st.session_state["quiz_stage"] = "done"
                st.rerun()
            else:
                st.session_state["quiz_stage"] = "final"
                st.rerun()
        return

    if stage == "final":
        st.markdown("### :orange[Final Quiz — Alphabetical Review]")
        final_keys = st.session_state["final_keys"]
        idx = st.session_state["final_index"]

        if idx >= len(final_keys):
            if st.session_state.get("should_save_results"):
                _save_quiz_result(spreadsheet, ws.title, "Completed")
                st.success("Congratulations! You have finished the quiz.")
                st.success("Your results have been saved and can be viewed in Quiz Results.")
            else:
                st.success("Congratulations! You have finished the final review.")
            st.session_state["quiz_stage"] = "done"
            return

        current_key = final_keys[idx]
        # Find all values for this key from quiz_items
        values_for_key = [v for k, v in st.session_state["quiz_items"] if k == current_key]

        st.write(f"Final quiz {idx + 1}/{len(final_keys)}")
        st.write(f"**Key:** {current_key}")
        st.write(f"**Value(s):** {'; '.join(values_for_key)}")

        with st.form("final_form", clear_on_submit=True):
            answer = st.text_input("Enter the key", key=f"final_answer_{idx}")
            submitted = st.form_submit_button("Submit Final Answer")

        if submitted:
            # Verify the answer is correct
            is_correct = answer.strip().casefold() == current_key.casefold()
            if is_correct:
                st.success("Correct!")
                st.session_state["final_incorrect_streak"] = 0
                st.session_state["final_index"] = idx + 1
            else:
                st.error(f"Incorrect. Correct key is: {current_key}")
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
        pass


def _page_quiz_results(spreadsheet):
    st.header("Quiz Results")
    rows = _get_results_rows(spreadsheet)
    if not rows:
        st.info("No quiz results yet.")
        return
    st.table(rows)


def _page_quiz_management(spreadsheet, ws):
    st.header("Quiz")
    quiz_tab, results_tab = st.tabs(["Quiz", "Quiz Results"])

    with quiz_tab:
        _page_quiz(spreadsheet, ws)

    with results_tab:
        _page_quiz_results(spreadsheet)


def main():
    st.set_page_config(page_title="Project D", page_icon="📘", layout="wide")
    _init_state()

    try:
        spreadsheet = _get_spreadsheet()
        ws = _ensure_active_worksheet(spreadsheet)
    except Exception as e:
        st.error(str(e))
        st.info("Set GS_CREDS and GS_SHEET in your .env file, then refresh.")
        return

    selected_page = _render_sidebar(spreadsheet, ws)

    if selected_page == "Worksheet":
        _page_worksheet_management(spreadsheet, ws)
    elif selected_page == "ABC":
        _page_abc_management(spreadsheet, ws)
    elif selected_page == "Quiz":
        _page_quiz_management(spreadsheet, ws)


if __name__ == "__main__":
    main()
