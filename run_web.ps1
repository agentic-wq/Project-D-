$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$venvActivate = Join-Path $projectRoot ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $venvActivate)) {
    Write-Error "Virtual environment activation script not found at: $venvActivate"
}

& $venvActivate

if (-not (Get-Command streamlit -ErrorAction SilentlyContinue)) {
    Write-Host "Streamlit not found in current environment. Installing requirements..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host "Starting Project D web UI..." -ForegroundColor Green
streamlit run web_app.py
