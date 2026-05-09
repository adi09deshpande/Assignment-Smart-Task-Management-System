$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not found. Run .\setup_windows.ps1 first."
    exit 1
}

if (-not (Test-Path ".env")) {
    Write-Host ".env was not found."
    Write-Host "Create .env in the project root, update DATABASE_URL, then run this script again."
    exit 1
}

$python = Join-Path $root ".venv\Scripts\python.exe"

Write-Host "Starting TaskFlow..."
& $python run.py
