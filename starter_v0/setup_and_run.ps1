#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup và chạy Day04 Lab Research Agent.
    Chạy từ bất kỳ đâu trong repo.
.EXAMPLE
    .\starter_v0\setup_and_run.ps1          # setup + run UI
    .\starter_v0\setup_and_run.ps1 -Check   # chỉ kiểm tra
    .\starter_v0\setup_and_run.ps1 -Eval    # chạy eval v3
#>

param(
    [switch]$Check,
    [switch]$Eval,
    [switch]$Chat
)

$ErrorActionPreference = "Stop"

# --- Tìm starter_v0 dir ---
$script_dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$starter = $script_dir
if (-not (Test-Path "$starter\app.py")) {
    Write-Error "Không tìm thấy app.py. Chạy script này từ bên trong hoặc chỉ định đường dẫn."
    exit 1
}

Write-Host "`n===== Day04 Lab — Research Agent Setup =====" -ForegroundColor Cyan
Write-Host "Working directory: $starter" -ForegroundColor Gray

# --- Tạo venv nếu chưa có ---
$venv_python = "$starter\.venv\Scripts\python.exe"
if (-not (Test-Path $venv_python)) {
    Write-Host "`n[1/3] Tạo virtual environment..." -ForegroundColor Yellow
    Set-Location $starter
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Tạo venv thất bại. Đảm bảo Python 3.9+ đã được cài."
        exit 1
    }
    Write-Host "      venv tạo thành công ✅" -ForegroundColor Green
} else {
    Write-Host "`n[1/3] venv đã tồn tại ✅" -ForegroundColor Green
}

# --- Install requirements ---
Write-Host "`n[2/3] Cài đặt requirements..." -ForegroundColor Yellow
Set-Location $starter
& $venv_python -m pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install thất bại."
    exit 1
}
Write-Host "      requirements installed ✅" -ForegroundColor Green

# --- Verify ---
Write-Host "`n[3/3] Kiểm tra..." -ForegroundColor Yellow
$streamlit_exe = "$starter\.venv\Scripts\streamlit.exe"
$sl_ok = Test-Path $streamlit_exe
Write-Host "      streamlit: $(if ($sl_ok) {'✅'} else {'❌ NOT FOUND'})"

# Check weather (no API key needed)
$weather_result = & $venv_python -c @"
import sys; sys.path.insert(0,'$($starter -replace '\\','/')');
from tools.weather.tool import get_weather
r = get_weather('Hanoi')
if r.get('error'):
    print('ERROR:', r['error'])
else:
    print('OK:', r['current']['temperature_c'], 'C')
"@ 2>&1
Write-Host "      weather tool: $weather_result"

# --- Dispatch ---
if ($Check) {
    Write-Host "`n===== Running project checker =====" -ForegroundColor Cyan
    & $venv_python "$starter\scripts\check_project.py"
    exit $LASTEXITCODE
}

if ($Eval) {
    Write-Host "`n===== Running eval (v3 base + group) =====" -ForegroundColor Cyan
    Set-Location $starter
    & $venv_python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json
    exit $LASTEXITCODE
}

if ($Chat) {
    Write-Host "`n===== Starting chat CLI =====" -ForegroundColor Cyan
    Set-Location $starter
    & $venv_python chat.py --provider openrouter --version v3
    exit $LASTEXITCODE
}

# Default: run Streamlit UI
Write-Host "`n===== Starting Streamlit UI =====" -ForegroundColor Cyan
Write-Host "URL: http://localhost:8501" -ForegroundColor Magenta
Write-Host "(Ctrl+C để dừng)" -ForegroundColor Gray
Set-Location $starter
& $streamlit_exe run app.py
