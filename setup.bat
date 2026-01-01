@echo off
REM ============================================================================
REM Trading Bot System - Windows Setup Script
REM ============================================================================
REM 
REM Ez a script Windows rendszeren beállítja a Trading Bot projektet:
REM 1. .env.template másolása .env fájllá
REM 2. Python dependency-k telepítése
REM 3. Adatbázis inicializálás
REM
REM ============================================================================

setlocal EnableDelayedExpansion

REM Színek a jobb olvashatóságért (Windows CMD korlátozottan támogatja)
color 0A

echo.
echo ===============================================================================
echo   Trading Bot System - Windows Setup
echo ===============================================================================
echo.

REM ============================================================================
REM 1. Környezeti fájl másolása
REM ============================================================================
echo [1/3] Környezeti fájl beállítása...

if exist ".env" (
    echo   ⚠️  .env fájl már létezik, átugrás...
) else (
    copy ".env.template" ".env" >nul 2>&1
    if exist ".env" (
        echo   ✅ .env fájl létrehozva
        echo   ⚠️  Kérlek szerkeszd a .env fájlt a saját beállításokkal!
    ) else (
        echo   ❌ HIBA: .env fájl nem hozható létre
        echo   Ellenőrizd, hogy .env.template létezik-e
        exit /b 1
    )
)

echo.

REM ============================================================================
REM 2. Python verzió ellenőrzése
REM ============================================================================
echo [2/3] Python verzió ellenőrzése...

python --version >nul 2>&1
if errorlevel 1 (
    echo   ❌ HIBA: Python nincs telepítve vagy nincs a PATH-ban
    echo   Töltsd le: https://www.python.org/downloads/
    echo   Minimum verzió: Python 3.11+
    exit /b 1
)

for /f "tokens=2" %%i in ('python -c "import sys; print(sys.version_info.major)"') do set PY_MAJOR=%%i
for /f "tokens=2" %%i in ('python -c "import sys; print(sys.version_info.minor)"') do set PY_MINOR=%%i

if "%PY_MAJOR%"=="3" (
    if "%PY_MINOR%" GEQ "11" (
        echo   ✅ Python 3.%PY_MINOR% -vagy újabb verzió detectálva
    ) else (
        echo   ⚠️  Figyelmeztetés: Python 3.%PY_MINOR% van telepítve
        echo   Ajánlott: Python 3.11 vagy újabb
    )
)

echo.

REM ============================================================================
REM 3. Dependency-k telepítése
REM ============================================================================
echo [3/4] Python dependency-k telepítése...

echo   pip install --upgrade pip...
pip install --upgrade pip >nul 2>&1

echo   Telepítem a csomagokat...
pip install -r requirements.txt >nul 2>&1

if errorlevel 1 (
    echo   ❌ HIBA: Csomag telepítés sikertelen
    echo   Próbáld manuelisan: pip install -r requirements.txt
    exit /b 1
) else (
    echo   ✅ Dependency-k telepítve
)

echo.

REM ============================================================================
REM 4. Adatbázis inicializálás (opcionális)
REM ============================================================================
echo [4/4] Adatbázis inicializálás...

set /p db_init="Szeretnéd inicializálni az adatbázist? (i/n): "

if /i "%db_init%"=="i" (
    echo   Adatbázis inicializálása...
    python init_db.py init
    
    if errorlevel 1 (
        echo   ⚠️  Figyelmeztetés: Az adatbázis inicializálás sikertelen
        echo   Ellenőrizd a PostgreSQL kapcsolatot a .env fájlban
    ) else (
        echo   ✅ Adatbázis inicializálva
    )
)

echo.
echo ===============================================================================
echo   Setup befejezve!
echo ===============================================================================
echo.
echo   Következő lépések:
echo   1. Szerkeszd a .env fájlt (adatbázis jelszó, API kulcsok)
echo   2. Indítsd a szervert: uvicorn main:app --reload --host 0.0.0.0 --port 8000
echo   3. Nyisd meg böngészőben: http://localhost:8000
echo.
echo   Hasznos parancsok:
echo   - Szerver indítása: uvicorn main:app --reload
echo   - Tesztek futtatása: pytest
echo   - Linting: black .
echo.
pause

endlocal
