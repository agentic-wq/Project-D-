# Implementation Guide — Project D

**Document Version:** 1.0  
**Date:** February 24, 2026  
**Status:** Active  

---

## 1. Introduction

This guide provides step-by-step instructions for developers and system administrators to set up, run, test, and deploy Project D in various environments.

---

## 2. Prerequisites

### 2.1 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|------------|
| **OS** | Windows 10, macOS 10.14+, Ubuntu 20.04+ | Windows 11, macOS 12+, Ubuntu 22.04+ |
| **Python** | 3.9 | 3.10+ |
| **RAM** | 4 GB | 8 GB |
| **Disk** | 2 GB free | 5 GB free |
| **Browser** | Chrome 90+, Firefox 88+, Safari 14+ | Chrome Latest, Firefox Latest |

### 2.2 Required Accounts & Access

- [ ] Google Cloud Project with Google Sheets API enabled
- [ ] Google Cloud service account with JSON credentials file
- [ ] GitHub account (for version control and collaboration)
- [ ] Spreadsheet shared with service account email

### 2.3 Required Software

```
1. Python 3.9+
   Download: https://www.python.org/downloads/
   Verify: python --version

2. Git
   Download: https://git-scm.com/downloads
   Verify: git --version

3. Chrome Browser (for Selenium)
   Download: https://www.google.com/chrome/
   Verify: chromium-browser --version (or chrome --version on Windows)

4. Google Chrome WebDriver (ChromeDriver)
   Download: https://chromedriver.chromium.org/
   - Ensure version matches your Chrome version
   - Add to PATH or store in project directory

5. pip (Python package manager)
   Usually included with Python
   Verify: pip --version
```

---

## 3. Installation & Setup

### 3.1 Clone Repository

```bash
# Navigate to desired directory
cd ~/Projects

# Clone from GitHub
git clone https://github.com/yourusername/project-d.git
cd project-d
```

### 3.2 Create Python Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux (Bash/Zsh):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Verify activation:**
```
(.venv) $ python --version
```

### 3.3 Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

**requirements.txt contents:**
```
gspread>=5.0.0
google-auth>=2.0.0
python-dotenv>=0.19.0
selenium>=4.0.0
webdriver-manager>=3.8.0
streamlit>=1.0.0
```

**Verify installation:**
```bash
python -c "import gspread, selenium, streamlit; print('All requirements installed ✓')"
```

### 3.4 Set Up Google Cloud Credentials

#### 3.4.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: Click dropdown → "New Project"
3. Name: "Project D" (or your choice)
4. Accept default settings, click "Create"

#### 3.4.2 Enable Required APIs

1. In Cloud Console, search for "Google Sheets API"
2. Click → Enable
3. Search for "Google Maps API"
4. Click → Enable

#### 3.4.3 Create Service Account

1. Go to "Credentials" (left sidebar)
2. Click "Create Credentials" → "Service Account"
3. Fill in:
   - **Service account name:** `project-d-sa`
   - **Service account ID:** `project-d-sa@[project-id].iam.gserviceaccount.com`
4. Click "Create and Continue"
5. Grant roles (optional for basic setup): Skip
6. Click "Done"

#### 3.4.4 Create & Download Service Account Key

1. In Credentials page, under Service Accounts, click `project-d-sa`
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Select "JSON" format
5. Click "Create" (file auto-downloads as `[project-id]-[random].json`)

#### 3.4.5 Configure Environment Variables

1. **Rename** downloaded JSON file (for convenience):
   ```bash
   mv [long-file-name].json gs-creds.json
   ```

2. **Place** in project root (or secure location):
   ```bash
   Project D/
   ├── .env
   ├── gs-creds.json          ← Place credentials here
   ├── web_app.py
   ├── app.py
   ├── requirements.txt
   └── ...
   ```

3. **Create** `.env` file in project root:
   ```
   GS_SHEET_ID="your-spreadsheet-id-here"
   GS_CREDENTIALS="gs-creds.json"
   STREAMLIT_SERVER_HEADLESS=false
   ```

4. **Get your Spreadsheet ID:**
   - Open Google Sheets
   - Create new spreadsheet (or reuse existing)
   - URL: `https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit#...`
   - Copy `[SHEET_ID]` part

5. **Share spreadsheet** with service account:
   - Copy service account email: `project-d-sa@[project-id].iam.gserviceaccount.com`
   - Open spreadsheet → Share → Paste email → Advanced → Give editor access

### 3.5 Verify Google Sheets Connection

```bash
# Run test script
python -c "
import gspread
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file('gs-creds.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
gc = gspread.authorize(creds)
sh = gc.open_by_key('[GS_SHEET_ID]')
print(f'✓ Connected to spreadsheet: {sh.title}')
print(f'✓ Worksheets: {[ws.title for ws in sh.worksheets()]}')
"
```

---

## 4. Running the Application

### 4.1 Development Mode (Local)

**Start Streamlit server:**
```bash
# Ensure .venv is activated
streamlit run web_app.py
```

**Expected output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.x:8501

  For better performance, install Pyarrow: pip install pyarrow
```

**Access the app:**
- Open browser: `http://localhost:8501`
- Begin using worksheets, ABC, and Quiz tabs

**Stop server:** Press `Ctrl+C` in terminal

### 4.2 Windows PowerShell Script

A convenience script is included:

**File: `run_web.ps1`**
```powershell
# Activate virtual environment
& ".\.venv\Scripts\Activate.ps1"

# Run Streamlit
streamlit run web_app.py
```

**Execute:**
```powershell
.\run_web.ps1
```

### 4.3 Configuration Tuning

**Streamlit config:** `.streamlit/config.toml`

```toml
[theme]
primaryColor = "#1f77d4"
backgroundColor = "#0e1117"
secondaryBackgroundColor = "#161b22"
textColor = "#c9d1d9"
font = "sans serif"

[client]
showErrorDetails = true
toolbarMode = "developer"

[logger]
level = "info"
```

**For production, adjust:**
```toml
[client]
showErrorDetails = false          # Hide technical details from users
toolbarMode = "minimal"           # Hide developer tools

[logger]
level = "warning"                 # Log only warnings and errors
```

---

## 5. Development Workflow

### 5.1 Making Changes

1. **Create feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Edit files** (web_app.py, app.py, etc.)

3. **Test locally:**
   ```bash
   streamlit run web_app.py
   ```

4. **Commit changes:**
   ```bash
   git add .
   git commit -m "Add my feature"
   ```

5. **Push to GitHub:**
   ```bash
   git push origin feature/my-feature
   ```

6. **Create Pull Request** on GitHub for code review

### 5.2 Code Organization

```
project-d/
├── web_app.py              ← Main Streamlit app (do not modify unless necessary)
├── app.py                  ← Utility functions (Google Maps scraping, etc.)
├── requirements.txt        ← Python dependencies
├── .env                    ← Environment variables (NOT in git)
├── gs-creds.json          ← Service account JSON (NOT in git)
├── run_web.ps1            ← Windows startup script
│
├── .streamlit/
│   └── config.toml        ← Streamlit configuration
│
├── docs/
│   ├── 01_Project_Documentation/  ← This documentation
│   ├── Business_Requirements.md
│   ├── Function_Inventory_Report.md
│   └── diagrams/
│       └── *.svg           ← Architecture diagrams
│
├── __pycache__/           ← Compiled Python (ignore)
├── .git/                  ← Git history (auto-maintained)
└── .gitignore            ← Files excluded from git
```

---

## 6. Testing

### 6.1 Manual Testing Checklist

**Worksheet Management:**
- [ ] Can select/create first worksheet
- [ ] Can list all worksheets
- [ ] Can create new worksheet
- [ ] Can rename worksheet
- [ ] Can delete worksheet

**ABC Management (CRUD):**
- [ ] Can create A–Z key with values
- [ ] Can create multiple values per key
- [ ] Can read/view all A–Z pairs
- [ ] Can update existing pair
- [ ] Can clear values (preserve key)
- [ ] Can delete pair entirely
- [ ] Google Maps integration works (optional)

**Quiz Workflows:**
- [ ] Practice stage displays all pairs
- [ ] Can navigate forward/backward in practice
- [ ] Quiz stage accepts correct answers
- [ ] Quiz stage rejects incorrect answers
- [ ] Adaptive difficulty triggers after 3 wrong answers
- [ ] Review timer displays and counts down correctly
- [ ] Input disabled while timer active
- [ ] Final stage requires alphabetical order
- [ ] Resets on any incorrect answer in Final
- [ ] Completion recorded to Google Sheets

**Feedback & UX:**
- [ ] Error messages are clear
- [ ] Success messages are displayed
- [ ] Feedback appears below form (not above)
- [ ] Progress indicators (e.g., "Key 7 of 26") shown
- [ ] No data loss on page refresh

### 6.2 Browser Compatibility Testing

```bash
# Test in multiple browsers
1. Chrome (primary)
   - Desktop: Windows, macOS, Linux
   - Mobile: iOS Safari (optional)
   
2. Firefox
   - Same platforms as Chrome
   
3. Safari (macOS/iOS only)
```

### 6.3 Edge Cases to Test

- Empty worksheet
- Worksheet with only A key (incomplete A–Z)
- Very long values (>500 chars)
- Special characters in keys/values (é, ñ, emoji)
- Rapid quiz submissions (spam click Submit)
- Network failure during quiz (simulate with DevTools)
- Google Sheets unavailable (mock API error)
- Missing .env variables
- Invalid service account credentials

---

## 7. Deployment

### 7.1 Deployment to Streamlit Cloud (Recommended for Simple Setup)

**Prerequisites:**
- GitHub account with repo containing project files
- Streamlit account (free tier available)

**Steps:**

1. **Push code to GitHub:**
   ```bash
   git push origin main
   ```

2. **Go to Streamlit Cloud:** https://streamlit.io/cloud

3. **Click "New App":**
   - Select repository: `your-username/project-d`
   - Select branch: `main`
   - Set main file path: `web_app.py`

4. **Configure Secrets:**
   - Streamlit Cloud → App settings → Secrets
   - Add contents of `.env`:
     ```
     GS_SHEET_ID = "your-spreadsheet-id"
     GS_CREDENTIALS = """
     {
         "type": "service_account",
         ...full JSON credentials...
     }
     """
     ```

5. **Deploy:**
   - Click "Deploy"
   - Share public URL with users

**Note:** Keep `.env` and `gs-creds.json` out of GitHub (add to `.gitignore`)

### 7.2 Deployment to Google Cloud Run (Containerized)

**Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

CMD ["streamlit", "run", "web_app.py"]
```

**Deploy:**
```bash
# Build and push Docker image
gcloud builds submit --tag gcr.io/[PROJECT_ID]/project-d

# Deploy to Cloud Run
gcloud run deploy project-d \
  --image gcr.io/[PROJECT_ID]/project-d \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GS_SHEET_ID="[SHEET_ID]" \
  --set-env-vars GS_CREDENTIALS="[JSON_string]"
```

### 7.3 Traditional Server Deployment (AWS EC2, DigitalOcean, etc.)

**Setup:**
1. SSH into server
2. Install Python 3.10+, Git
3. Clone repo: `git clone https://github.com/...`
4. Follow Installation steps (3.1–3.5)
5. Create systemd service file:

**File: `/etc/systemd/system/project-d.service`**
```ini
[Unit]
Description=Project D Streamlit Application
After=network.target

[Service]
User=app-user
WorkingDirectory=/home/app-user/project-d
ExecStart=/home/app-user/project-d/.venv/bin/streamlit run web_app.py --server.port=8501
Restart=always

[Install]
WantedBy=multi-user.target
```

**Start service:**
```bash
sudo systemctl enable project-d
sudo systemctl start project-d
```

---

## 8. Monitoring & Maintenance

### 8.1 Health Checks

**Monthly:**
- [ ] Verify Google Sheets API still works
- [ ] Check Streamlit version for security updates
- [ ] Review error logs for recurring issues
- [ ] Validate Chrome/ChromeDriver compatibility

**Logging:**
```bash
# View Streamlit logs
tail -f /var/log/project-d.log  # If using systemd

# View Python exceptions
streamlit run web_app.py --logger.level=debug
```

### 8.2 Dependency Updates

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade gspread

# Update all packages (caution: may break compatibility)
pip install --upgrade -r requirements.txt
```

### 8.3 Backup Strategy

**Google Sheets backups:**
- Automatic: Google Drive versioning (built-in)
- Manual: File → Download → Microsoft Excel

**Code backups:**
- Automatic: GitHub (continuous)
- Local: Daily commits to feature branches

---

## 9. Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'gspread'"

**Solution:**
```bash
# Activate venv
source .venv/bin/activate  # macOS/Linux
.\.venv\Scripts\Activate.ps1  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

---

### Issue: "Worksheet not found"

**Solution:**
1. Verify spreadsheet is shared with service account
2. Check `GS_SHEET_ID` in `.env` is correct
3. Run verification script:
   ```bash
   python -c "
   import gspread
   from google.oauth2.service_account import Credentials
   creds = Credentials.from_service_account_file('gs-creds.json')
   gc = gspread.authorize(creds)
   sh = gc.open_by_key('[SHEET_ID]')
   print(sh.worksheets())
   "
   ```

---

### Issue: "Invalid credentials" or "PERMISSION_DENIED"

**Solution:**
1. Download fresh service account JSON from Google Cloud Console
2. Replace `gs-creds.json`
3. Re-share spreadsheet with service account email (it may have changed)
4. Verify scopes in service account include `https://www.googleapis.com/auth/spreadsheets`

---

### Issue: Streamlit not opening in browser

**Solution:**
1. Check terminal output for URL (usually `http://localhost:8501`)
2. Copy-paste URL into browser
3. If still not working, try different port:
   ```bash
   streamlit run web_app.py --server.port=8502
   ```
4. Verify no firewall is blocking the port

---

### Issue: Quiz timer not displaying

**Solution:**
1. Verify browser console for JavaScript errors (F12)
2. Check `.streamlit/config.toml` for proper theme settings
3. Try hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (macOS)

---

### Issue: Google Maps scraping fails

**Solution:**
1. Verify Chrome/ChromeDriver versions match:
   ```bash
   chromium-browser --version
   chromedriver --version  # or check webdriver_manager logs
   ```
2. Check internet connection
3. Try again (Google may rate-limit queries)
4. Use manual entry fallback instead of Google Maps

---

## 10. Performance Optimization

### 10.1 Quick Wins

```python
# In web_app.py, add caching for expensive operations
@st.cache_data
def load_quiz_data(worksheet):
    return _read_abc(worksheet)

# Verify result: data loads instantly on re-access
```

### 10.2 Advanced Optimization

- Implement connection pooling for Google Sheets
- Add Redis caching for frequently accessed worksheets
- Batch Google Sheets writes (multiple updates in single API call)
- Lazy-load results table (paginate instead of loading all 10K rows)

---

## 11. Security Checklist

- [ ] `.env` file in `.gitignore` (credentials never in Git)
- [ ] `gs-creds.json` in `.gitignore`
- [ ] Service account restricted to only Sheets/Maps APIs
- [ ] Spreadsheet shared only with service account (not public)
- [ ] Input sanitization in quiz submission (trim, case-insensitive)
- [ ] No sensitive data logged to console
- [ ] HTTPS enabled in production (if using custom domain)

---

## Appendix A: Environment Variables Reference

| Variable | Example | Purpose |
|----------|---------|---------|
| `GS_SHEET_ID` | `1v5-0a3bX7...` | Google Sheets ID |
| `GS_CREDENTIALS` | `gs-creds.json` | Path to service account JSON |
| `STREAMLIT_SERVER_HEADLESS` | `true` / `false` | Run without browser |

---

## Appendix B: Quick Reference Commands

```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.\.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run web_app.py

# Check installed packages
pip list

# Freeze current dependencies
pip freeze > requirements.txt

# Test Google Sheets connection
python test_sheets_connection.py

# Deactivate virtual environment
deactivate
```

---

**Document Owner:** DevOps Engineer / Lead Developer  
**Last Updated:** February 24, 2026  
**Next Review Date:** [After first production deployment]
