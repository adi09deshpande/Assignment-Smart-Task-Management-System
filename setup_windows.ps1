$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

$python = Join-Path $root ".venv\Scripts\python.exe"

Write-Host "Upgrading pip..."
& $python -m pip install --upgrade pip

Write-Host "Installing dependencies..."
& $python -m pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host ".env was not found."
    Write-Host "Create a .env file in the project root before running the app."
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "Update DATABASE_URL in .env before running the app."
