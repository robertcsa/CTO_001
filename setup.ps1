#!/usr/bin/env pwsh
# ============================================================================
# Trading Bot System - PowerShell Setup Script
# ============================================================================
#
# Ez a script Windows PowerShell-ben beállítja a Trading Bot projektet:
# 1. .env.template másolása .env fájllá
# 2. Python dependency-k telepítése
# 3. Adatbázis inicializálás
#
# Futtatás: .\setup.ps1
# Ha a szkriptek le vannak tiltva, használd: Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
# ============================================================================

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Write-Host "`n===============================================================================" -ForegroundColor Cyan
Write-Host "  Trading Bot System - Windows Setup (PowerShell)" -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 1. Környezeti fájl másolása
# ============================================================================
Write-Host "[1/4] Környezeti fájl beállítása..." -ForegroundColor Yellow

if (Test-Path ".env") {
    Write-Host "  ⚠️  .env fájl már létezik, átugrás..." -ForegroundColor Yellow
} else {
    try {
        Copy-Item ".env.template" ".env" -ErrorAction Stop
        Write-Host "  ✅ .env fájl létrehozva" -ForegroundColor Green
        Write-Host "  ⚠️  Kérlek szerkeszd a .env fájlt a saját beállításokkal!" -ForegroundColor Yellow
    } catch {
        Write-Host "  ❌ HIBA: .env fájl nem hozható létre" -ForegroundColor Red
        Write-Host "  Ellenőrizd, hogy .env.template létezik-e" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# ============================================================================
# 2. Python verzió ellenőrzése
# ============================================================================
Write-Host "[2/4] Python verzió ellenőrzése..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "  ✅ $pythonVersion detectálva" -ForegroundColor Green
    
    $versionInfo = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    $major, $minor = $versionInfo.Split('.')
    
    if ([int]$major -eq 3 -and [int]$minor -ge 11) {
        Write-Host "  ✅ Python 3.$minor - kompatibilis verzió" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Figyelmeztetés: Python 3.$minor van telepítve (ajánlott: 3.11+)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ HIBA: Python nincs telepítve vagy nincs a PATH-ban" -ForegroundColor Red
    Write-Host "  Töltsd le: https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "  Minimum verzió: Python 3.11+" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# 3. Dependency-k telepítése
# ============================================================================
Write-Host "[3/4] Python dependency-k telepítése..." -ForegroundColor Yellow

Write-Host "  Pip upgrade..." -ForegroundColor Gray
try {
    pip install --upgrade pip --quiet 2>&1 | Out-Null
    Write-Host "  ✅ Pip upgrade kész" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Figyelmeztetés: Pip upgrade sikertelen" -ForegroundColor Yellow
}

Write-Host "  Csomagok telepítése..." -ForegroundColor Gray
try {
    pip install -r requirements.txt 2>&1 | Out-Null
    Write-Host "  ✅ Dependency-k telepítve" -ForegroundColor Green
} catch {
    Write-Host "  ❌ HIBA: Csomag telepítés sikertelen" -ForegroundColor Red
    Write-Host "  Próbáld manuelisan: pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# 4. Adatbázis inicializálás (opcionális)
# ============================================================================
Write-Host "[4/4] Adatbázis inicializálás..." -ForegroundColor Yellow

$dbInit = Read-Host "  Szeretnéd inicializálni az adatbázist? (i/n)"

if ($dbInit.ToLower() -eq 'i' -or $dbInit.ToLower() -eq 'y') {
    Write-Host "  Adatbázis inicializálása..." -ForegroundColor Gray
    try {
        python init_db.py init
        Write-Host "  ✅ Adatbázis inicializálva" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  Figyelmeztetés: Az adatbázis inicializálás sikertelen" -ForegroundColor Yellow
        Write-Host "  Ellenőrizd a PostgreSQL kapcsolatot a .env fájlban" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "  Setup befejezve!" -ForegroundColor Green
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Következő lépések:" -ForegroundColor White
Write-Host "  1. Szerkeszd a .env fájlt (adatbázis jelszó, API kulcsok)" -ForegroundColor White
Write-Host "  2. Indítsd a szervert: uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host "  3. Nyisd meg böngészőben: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "  Hasznos parancsok:" -ForegroundColor White
Write-Host "  - Szerver indítása: uvicorn main:app --reload" -ForegroundColor Gray
Write-Host "  - Tesztek futtatása: pytest" -ForegroundColor Gray
Write-Host "  - Linting: black ." -ForegroundColor Gray
Write-Host ""
