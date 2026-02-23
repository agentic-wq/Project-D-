# LangGraph ABC Starter (Python)           

A minimal LangGraph CLI that preloads a small key/value store into the graph state.

Usage
-----
1. Create and activate a Python environment (recommended).
2. Install dependencies:

   pip install -r requirements.txt

3. Run:

   python app.py
   python app.py --set color blue

Web UI
------
You can run a browser-based frontend for worksheet management, ABC operations, quiz, and quiz results:

```bash
streamlit run web_app.py
```

Or on Windows PowerShell, run the one-command launcher:

```powershell
.\run_web.ps1
```

The Web UI uses the same Google Sheets environment variables (`GS_CREDS`, `GS_SHEET`, optional `GS_WORKSHEET`).

Web UI Screenshots
------------------
Add screenshots to `docs/screenshots/` and keep these names for automatic display in this section:

- `menu-overview.png`
- `worksheet-management.png`
- `quiz-flow.png`
- `quiz-results.png`

<!-- Replace placeholders below once image files exist -->
![Web UI - Menu Overview](docs/screenshots/menu-overview.png)
![Web UI - Worksheet Management](docs/screenshots/worksheet-management.png)
![Web UI - Quiz Flow](docs/screenshots/quiz-flow.png)
![Web UI - Quiz Results](docs/screenshots/quiz-results.png)

What it does
------------
- Preloads `abc` with: `name: Alice`, `role: developer`, `project: Project D`.
- Graph nodes merge any `to_set` values into the `abc` store and then print the final store.

Files
-----
- `app.py` — example LangGraph `StateGraph` with preloaded key/value pairs.
- `web_app.py` — Streamlit frontend for the Project D workflows.
- `requirements.txt` — lists `langgraph`.

Google Sheets persistence
-------------------------
To enable saving/loading to Google Sheets, provide a service account credentials JSON and the spreadsheet ID. Share the spreadsheet with the service account email. Then run:

```bash
python app.py --gs-creds path/to/creds.json --gs-sheet your_spreadsheet_id
```

The app will load existing key/value pairs (two-column sheet) into the graph at start and overwrite the sheet with the final `abc` content at the end.

By default, writes do **not** overwrite an existing worksheet tab. The app creates a new worksheet tab name when saving/importing data. To explicitly allow overwrite of the configured worksheet, pass:

```bash
python app.py --gs-creds path/to/creds.json --gs-sheet your_spreadsheet_id --gs-worksheet Sheet1 --gs-overwrite
```

You can also set `GS_OVERWRITE=true` in the environment.

Notes
-----
This is a minimal starting point — tell me if you want persistence, an HTTP API, or extra nodes for read/write operations.