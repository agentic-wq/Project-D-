# Technical Architecture — Project D

**Document Version:** 1.0  
**Date:** February 24, 2026  
**Status:** Active  

---

## 1. Introduction

This document describes the technical architecture of Project D, including technology stack, system components, data flow, design patterns, and deployment strategy.

---

## 2. Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | Streamlit | 1.x+ | Web UI framework (Python-based, no HTML/CSS/JS required) |
| **Backend** | Python 3.x | 3.9+ | Core application logic |
| **State Management** | Streamlit session_state | Built-in | Quiz progression, form state, timers |
| **Data Persistence** | Google Sheets API | v4 | A–Z pairs, quiz results |
| **Google Auth** | google-auth | 2.x+ | Service account authentication |
| **Sheets Client** | gspread | 5.x+ | Google Sheets interaction library |
| **Web Scraping** | Selenium | 4.x+ | Google Maps place name extraction |
| **Browser Driver** | ChromeDriver | Latest | Selenium WebDriver for Chrome |
| **Package Manager** | pip | Latest | Python dependency management |
| **Version Control** | Git/GitHub | Latest | Code repository and collaboration |

---

## 3. High-Level System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        User Browser                               │
│                    (Streamlit Web UI)                             │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ HTTP
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Streamlit Application                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Frontend UI Components                                   │   │
│  │  - Worksheet Management (CRUD tabs)                      │   │
│  │  - ABC Management (Create, Read, Update, Delete)         │   │
│  │  - Quiz Interface (Practice, Quiz, Final stages)         │   │
│  │  - Results Dashboard                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                 │                                │
│  ┌──────────────────────────────┼──────────────────────────────┐ │
│  │  Core Application Logic       │                              │ │
│  │  ┌──────────────────────────────────────────────────────┐   │ │
│  │  │  web_app.py (Main Module, ~710 lines)               │   │ │
│  │  │  - _page_quiz(): Quiz controller with 3 stages      │   │ │
│  │  │  - _read_abc(): Read A–Z from Sheets                │   │ │
│  │  │  - _save_abc(): Write A–Z to Sheets                 │   │ │
│  │  │  - Quiz submission & validation logic                │   │ │
│  │  │  - Adaptive difficulty algorithm                     │   │ │
│  │  │  - Review timer management                           │   │ │
│  │  └──────────────────────────────────────────────────────┘   │ │
│  │                                                               │ │
│  │  ┌──────────────────────────────────────────────────────┐   │ │
│  │  │  app.py (Utility Module, ~130 lines)                │   │ │
│  │  │  - fetch_related_items(): Google Maps scraping       │   │ │
│  │  │    ├── is_valid_place_name(): validation helper      │   │ │
│  │  │    └── collect_place_names(): DOM extraction         │   │ │
│  │  └──────────────────────────────────────────────────────┘   │ │
│  │                                                               │ │
│  │  ┌──────────────────────────────────────────────────────┐   │ │
│  │  │  Session State Management                            │   │ │
│  │  │  - Quiz progression (remaining keys, submitted)      │   │ │
│  │  │  - Quiz feedback and timers                          │   │ │
│  │  │  - Current worksheet context                         │   │ │
│  │  └──────────────────────────────────────────────────────┘   │ │
│  └──────────────────────────────┼──────────────────────────────┘ │
│                                 │                                │
│  ┌──────────────────────────────┼──────────────────────────────┐ │
│  │  External Integrations       │                              │ │
│  └──────────────────────────────┼──────────────────────────────┘ │
└─────────────────────────────────┼──────────────────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │   Google Sheets  │  │  Google Maps     │  │   Chrome Browser │
    │   API (gspread)  │  │  (Selenium +     │  │   (WebDriver)    │
    │                  │  │   ChromeDriver)  │  │                  │
    │ - A–Z Pairs      │  │                  │  │ - DOM scraping   │
    │ - Quiz Results   │  │ - Place names    │  │ - Navigation     │
    │                  │  │ - Data validation│  │                  │
    └──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## 4. Component Architecture

### 4.1 Core Components

#### **Frontend UI Layer (Streamlit)**
- **Responsibility:** Render UI, capture user input, display feedback
- **Components:**
  - Sidebar navigation (tabs: Worksheet, ABC, Quiz, Results)
  - Worksheet management interface
  - ABC CRUD interfaces
  - Quiz form (text input + submit button)
  - Feedback display area
  - Review timer display
  - Results table

#### **Application Logic Layer (web_app.py)**
- **Responsibility:** Orchestrate workflows, quiz logic, state management
- **Key Functions:**
  - `_page_quiz(spreadsheet, ws)`: Main quiz controller
    - Manages 3 stages: Practice, Quiz, Final
    - Handles form submission and validation
    - Implements adaptive difficulty
    - Manages review timer countdown
    - Displays feedback consistently
  - `_read_abc(ws)`: Fetch A–Z pairs from current worksheet
  - `_save_abc(ws, abc_dict)`: Persist A–Z pairs to Google Sheets
  - ABC CRUD operations (create, read, update, delete)
  - Worksheet management (select, list, rename, delete)

#### **Utility Layer (app.py)**
- **Responsibility:** Provide reusable, UI-agnostic functions
- **Key Function:**
  - `fetch_related_items(query, limit=20)`: Google Maps scraping utility
    - Validates place names
    - Handles Selenium browser lifecycle
    - Returns deduplicated list of place names

#### **Session State Management**
- **Responsibility:** Persist quiz progression and UI state across Streamlit reruns
- **State Variables:**
  - `quiz_items`: Full list of A–Z pairs (practice/quiz source)
  - `quiz_remaining`: Keys not yet completed
  - `quiz_required`: Dict mapping key → required correct attempts
  - `quiz_submitted_values`: Dict mapping key → [already-submitted values]
  - `quiz_streaks`: Dict mapping key → consecutive correct count
  - `quiz_review_timer`: Epoch timestamp of timer expiration (None if inactive)
  - `quiz_feedback`: Dict with type, message, warning (cleared each rerun)
  - `current_worksheet`: Name of active worksheet
  - `current_spreadsheet_id`: Google Sheets ID for active spreadsheet

### 4.2 External Services

#### **Google Sheets API (gspread)**
- **Purpose:** Persistent A–Z data and quiz results storage
- **Authentication:** Service account credentials (JSON file)
- **Operations:**
  - Fetch worksheet list
  - Read cell ranges (A–Z pairs)
  - Write cell ranges (A–Z pairs, quiz results)
  - Worksheet creation/deletion/renaming
- **Error Handling:** Try-catch with user-friendly fallback messages
- **Caching:** Session-level caching (reload on demand)

#### **Google Maps Web Scraping (Selenium)**
- **Purpose:** Auto-populate knowledge set values for a given key
- **Trigger:** User selects "Google Maps" in Create workflow
- **Implementation:**
  - Launch headless Chrome via ChromeDriver
  - Navigate to Google Maps search for query
  - Extract place names from DOM
  - Validate place names (filter noise)
  - Return deduplicated list
- **Cleanup:** Gracefully close browser after extraction
- **Error Handling:** Fallback to manual entry if scraping fails

---

## 5. Data Flow Diagrams

### 5.1 Quiz Submission Flow

```
User Submits Answer
        │
        ▼
┌──────────────────────────┐
│ Validate Input           │
│ - Non-empty?             │
│ - Length reasonable?      │
└──────────────────────────┘
        │
        ▼
┌──────────────────────────┐
│ Check Correctness        │
│ answer ? in values[key]  │
└──────────────────────────┘
        │
    ┌───┴────────────────────┐
    │                        │
  CORRECT                 INCORRECT
    │                        │
    ▼                        ▼
┌────────────────┐   ┌───────────────────────┐
│ Check if       │   │ Increment wrong count │
│ Already        │   │ If 3rd wrong:         │
│ Submitted      │   │   - Activate timer    │
└────────────────┘   │   - Double required   │
    │                │     correct attempts  │
 ┌──┴──┐         └───────────────────────┘
 │     │              │
YES    NO             │
 │     │              │
 ▼     ▼              ▼
ERROR SUCCESS    ┌─────────────┐
MSG   + NEXT      │ Store and   │
      QUESTION    │ Display Err │
                  │ Feedback    │
                  └─────────────┘
```

### 5.2 Review Timer Flow

```
Wrong Answer Count Reaches 3
        │
        ▼
┌─────────────────────────────┐
│ Activate Timer              │
│ quiz_review_timer =         │
│ time.time() + 45            │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ Display Timer Widget        │
│ - Disable input/button      │
│ - Show countdown (45 → 0)   │
│ - Show warning message      │
└─────────────────────────────┘
        │
┌───────┴────────────┐
│   Sleep 0.5 sec    │
│   Check elapsed    │
│   Rerun if active  │
└───────┴────────────┘
        │
    ┌───┴──────┐
    │          │
  TIMER      TIMER
  ACTIVE     EXPIRED
    │          │
    ▼          ▼
  RERUN    CLEAR TIMER
  & SLEEP
    │
    └──→ Loop until expired
```

### 5.3 Google Sheets Sync Flow

```
User Completes Quiz (All 3 Stages)
        │
        ▼
┌──────────────────────────────┐
│ Create completion record     │
│ - Timestamp: now()           │
│ - Worksheet: session state   │
│ - Status: "Completed"        │
└──────────────────────────────┘
        │
        ▼
┌──────────────────────────────┐
│ Write to "Quiz Results" WS   │
│ via Google Sheets API        │
└──────────────────────────────┘
        │
        ▼
┌──────────────────────────────┐
│ Handle Result                │
├──────────────┬───────────────┤
│ Success      │ Failure       │
├──────────────┼───────────────┤
│ Display OK   │ Log error     │
│ Show record  │ Retry option  │
└──────────────┴───────────────┘
```

---

## 6. Database & Data Storage

### 6.1 Google Sheets Structure

**Spreadsheet Layout:**
```
Spreadsheet ID: [stored in .env as GS_SPREADSHEET_ID]
Auth: Service account (JSON credentials in .env)

Worksheet 1: "Spanish 101" (user-created)
  A          B
  ─────────────────
  A        | Apple, Apricot
  B        | Banana, Berry
  C        | Cherry, Cantaloupe
  ...

Worksheet 2: "Biology Terms" (user-created)
  A          B
  ─────────────────
  A        | Amino acid, Antibody
  B        | Bacteria, Base
  ...

Worksheet N: "Quiz Results" (auto-created)
  A                  B                C
  ─────────────────────────────────────────
  Timestamp          Worksheet Name   Status
  2026-02-24 14:30   Spanish 101      Completed
  2026-02-24 15:45   Biology Terms    Completed
```

**Data Format:**
- **Keys:** Single A–Z letter (column A, required)
- **Values:** Comma-separated or tab-separated strings (column B, multiple per key supported)
  - Example: "Apple, Apricot, Avocado" or ["Apple", "Apricot", "Avocado"]
- **Timestamps:** YYYY-MM-DD HH:MM:SS format
- **Status:** Enum ("Completed", "In Progress", optional)

### 6.2 No Traditional Database

**Rationale:**
- Google Sheets provides sufficient I/O performance for single-user loads
- No SQL setup required (zero infrastructure burden)
- Built-in versioning and audit trail via Google Drive
- Multi-platform access (any spreadsheet viewer)

**Scaling Plan:**
If data exceeds 10K+ A–Z pairs:
- Migrate to PostgreSQL or Cloud Firestore
- Implement connection pooling and caching
- Keep Google Sheets as optional read-only export

---

## 7. Design Patterns

### 7.1 Streamlit Rerun Pattern
- **Pattern:** Continuous rerun (user interaction triggers full page rerun)
- **Usage:** Quiz submission, timer countdown, state updates
- **Implementation:** `st.rerun()` after critical updates
- **Challenge:** Maintain state across reruns via `session_state`
- **Solution:** Explicit session_state management for persistence

### 7.2 Session State Management
- **Pattern:** Centralized state store (Streamlit `session_state`)
- **Usage:** Quiz progression, feedback, timers
- **Implementation:**
  ```python
  if 'quiz_items' not in st.session_state:
      st.session_state.quiz_items = load_default_quiz_data()
  ```
- **Benefit:** Immutable state across reruns without re-fetching from API

### 7.3 Timer Pattern (Polling)
- **Pattern:** Epoch-based timer with continuous polling
- **Implementation:**
  ```python
  timer_expiry = time.time() + 45  # 45 seconds from now
  while time.time() < timer_expiry:
      remaining = int(timer_expiry - time.time())
      st.metric("Review Timer", f"{remaining} sec")
      time.sleep(0.5)
      st.rerun()
  ```
- **Benefit:** Non-blocking, smooth countdown display every 500ms

### 7.4 Validation Pipeline
- **Pattern:** Layered validation (syntax → business logic → persistence)
- **Usage:** Quiz submission, worksheet operations
- **Implementation:**
  1. Input validation (non-empty, length)
  2. Business logic validation (correct answer check)
  3. State validation (duplicate submission check)
  4. Persistence validation (Google Sheets error handling)

### 7.5 Graceful Degradation
- **Pattern:** Try-catch with user-friendly fallback messaging
- **Usage:** Google Sheets API failures, Selenium scraping errors
- **Implementation:**
  ```python
  try:
      data = gspread_client.fetch_range(worksheet)
  except APIError as e:
      st.error("Failed to load data. Please check credentials and try again.")
      return default_empty_state
  ```

---

## 8. Security Architecture

### 8.1 Credentials & Secrets

**Service Account Authentication:**
- Google service account JSON file (kept in `.env` or environment variables)
- Never committed to version control
- Scoped to only Google Sheets & Maps APIs
- Rotated periodically

**Environment Variables (.env):**
```
GS_SHEET_ID="[spreadsheet-id]"
GS_CREDENTIALS="[json-credentials-path]"
GS_CREDS_JSON="[raw-json-contents-optional]"
STREAMLIT_SERVER_HEADLESS=true
```

### 8.2 API Rate Limiting & Quotas

**Google Sheets API:**
- Standard quota: 500 requests/100 seconds per project
- Mitigation: Session-level caching, batch operations
- Monitoring: Log API call counts

**Google Maps Scraping (Selenium):**
- No official API quota (web scraping)
- Rate limit: 1 request per query session
- Cleanup: Graceful browser closure to avoid resource leaks

### 8.3 Data Privacy & Access Control

**Single-User Model:**
- No multi-user authentication (shared notebook context)
- All users share same Google service account
- No per-user data isolation (not currently implemented)

**Future Multi-User Considerations:**
- Add OAuth2 user authentication
- Implement per-user worksheet isolation
- Audit logging per user

### 8.4 Input Sanitization

- Quiz answer input: Stripped, case-insensitive comparison
- Worksheet names: Validated against API constraints
- Google Maps queries: URL-encoded before browser navigation

---

## 9. Deployment Architecture

### 9.1 Deployment Environment

**Current:** Single-user, local/laptop deployment via Streamlit

**Streamlit Execution:**
```
User executes: streamlit run web_app.py
  ▼
Streamlit server starts (localhost:8501)
  ▼
Browser opens to http://localhost:8501
  ▼
User interacts → reruns → state persists per browser session
```

### 9.2 Production Deployment Options

**Option A: Streamlit Community Cloud (Easiest)**
- Host directly from GitHub repository
- Automatic deployments on push
- Limitations: Community tier has resource caps
- Cost: Free to Pro tiers

**Option B: Docker + Cloud Run (Google Cloud)**
- Build Docker image with Python + dependencies
- Deploy to Google Cloud Run (serverless)
- Cost: Pay per execution

**Option C: Traditional Server (VM)**
- Deploy to VM (AWS EC2, Google Compute Engine, DigitalOcean, etc.)
- Run `streamlit run` as systemd service
- Cost: Continuous VM rental

### 9.3 Environment Configuration

**Development:**
```
STREAMLIT_SERVER_HEADLESS = False
STREAMLIT_LOGGER_LEVEL = debug
GS_CREDENTIALS = path/to/local/creds.json
```

**Production:**
```
STREAMLIT_SERVER_HEADLESS = True
STREAMLIT_LOGGER_LEVEL = info
GS_CREDENTIALS = environment-variable-injected
TLS_ENABLED = True (if behind reverse proxy)
```

---

## 10. Performance Considerations

| Operation | Target | Strategy |
|-----------|--------|----------|
| **Quiz submission** | <500ms | Async validation, session caching |
| **Worksheet load** | <1s | Session-level cache, lazy loading |
| **Page render** | <2s | Streamlit native optimization |
| **Google Sheets write** | <2s | Batch writes, connection pooling (future) |
| **Google Maps scrape** | <5s | Headless browser, selector optimization |

---

## 11. Monitoring & Logging

**Current:** Basic error logging to console/Streamlit logs

**Future Enhancements:**
- Structured logging (JSON format)
- Error tracking (Sentry integration)
- Performance metrics (New Relic, CloudWatch)
- User session analytics

---

## 12. Scalability & Future Expansion

### 12.1 Current Bottlenecks
1. Single-user session (no multi-user support)
2. Google Sheets API rate limits (500 requests/100 sec)
3. Selenium scraping performance (5-10 sec per Google Maps query)

### 12.2 Scaling Strategies
1. **Multi-User:** Add user authentication (OAuth2), per-user worksheet isolation
2. **Database:** Migrate to PostgreSQL for >10K pairs, implement connection pooling
3. **Caching:** Redis or memcached for frequent data access
4. **Async:** Task queue (Celery) for long-running operations (Google Maps scraping)
5. **CDN:** Static asset caching if UI components grow

---

## 13. Technology Rationale

| Technology | Why Chosen | Trade-offs |
|-----------|-----------|-----------|
| **Streamlit** | Rapid Python web UI, no HTML/CSS/JS needed | Limited advanced customization, rerun model can be inefficient |
| **Google Sheets** | No database setup, multi-platform access, built-in versioning | API rate limits, not optimal for high-concurrency |
| **Selenium** | Reliable web scraping, handles dynamic JavaScript | Slower than parsing APIs, resource-intensive browser |
| **Python** | Fast development, rich data science libraries | Not ideal for high-concurrency services |

---

**Document Owner:** Lead Developer / Architect  
**Last Updated:** February 24, 2026  
**Next Review Date:** [Before scaling efforts or major architectural changes]
