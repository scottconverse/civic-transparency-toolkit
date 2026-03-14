@echo off
REM ============================================================
REM Build script for Civic Transparency Toolkit (Windows)
REM Creates a standalone .exe using PyInstaller
REM
REM  >>> CHANGE THIS VERSION NUMBER FOR EACH BUILD <<<
REM ============================================================
set VERSION=v1.0
REM ============================================================

echo.
echo  Civic Transparency Toolkit — Build %VERSION%
echo  ============================================
echo.

REM --- Find Python ---
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON=python
    goto :found
)

where python3 >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON=python3
    goto :found
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON=py
    goto :found
)

REM Check common install locations (newest first)
for %%V in (314 313 312 311 310 39) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set PYTHON=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe
        goto :found
    )
)
for %%V in (314 313 312 311) do (
    if exist "C:\Python%%V\python.exe" (
        set PYTHON=C:\Python%%V\python.exe
        goto :found
    )
)

REM Check Microsoft Store Python
for /f "delims=" %%i in ('where /r "%LOCALAPPDATA%\Microsoft\WindowsApps" python*.exe 2^>nul') do (
    set PYTHON=%%i
    goto :found
)

echo.
echo ERROR: Python not found!
echo.
echo Please do ONE of the following:
echo.
echo   Option A: Install Python from python.org
echo             IMPORTANT: Check "Add Python to PATH" during install
echo.
echo   Option B: If Python is already installed, open a NEW terminal and run:
echo             python --version
echo             If that works, try running this script again from that terminal.
echo.
pause
exit /b 1

:found
echo Found Python: %PYTHON%
"%PYTHON%" --version
echo.

REM --- Check for duplicate version ---
if exist "dist\CivicTransparencyToolkit-%VERSION%" (
    echo.
    echo  WARNING: dist\CivicTransparencyToolkit-%VERSION% already exists!
    echo  If you continue, it will be REPLACED.
    echo.
    set /p CONFIRM="  Type Y to overwrite, or anything else to cancel: "
)
if defined CONFIRM (
    if /i not "%CONFIRM%"=="Y" (
        echo Build cancelled. Change the VERSION at the top of build.bat and try again.
        set CONFIRM=
        pause
        exit /b 0
    )
    rmdir /s /q "dist\CivicTransparencyToolkit-%VERSION%"
    set CONFIRM=
)

echo Step 1 of 6: Installing dependencies...
"%PYTHON%" -m pip install --upgrade pip
"%PYTHON%" -m pip install -r requirements.txt
"%PYTHON%" -m pip install pyinstaller
echo.

echo Step 2 of 6: Clearing cached bytecode...
REM Remove __pycache__ and .pyc files so PyInstaller compiles fresh source
if exist "__pycache__" rmdir /s /q "__pycache__"
for /d /r . %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc >nul 2>&1
REM Also clear PyInstaller's build cache
if exist "build" rmdir /s /q "build"
echo   Cleared all Python and PyInstaller caches.
echo.

echo Step 3 of 6: Building executable...
"%PYTHON%" -m PyInstaller ^
    --name "CivicTransparencyToolkit" ^
    --onedir ^
    --windowed ^
    --icon "assets\icon.ico" ^
    --add-data "prompts;prompts" ^
    --add-data "templates;templates" ^
    --hidden-import "yt_dlp" ^
    --hidden-import "youtube_transcript_api" ^
    --hidden-import "docx" ^
    --hidden-import "docx.shared" ^
    --hidden-import "docx.enum" ^
    --hidden-import "docx.enum.text" ^
    --hidden-import "docx.oxml" ^
    --hidden-import "docx.oxml.ns" ^
    --noconfirm ^
    --clean ^
    main.py
echo.

if exist "dist\CivicTransparencyToolkit\CivicTransparencyToolkit.exe" (
    echo Step 4 of 6: Copying extras and source code...
    copy "README.txt" "dist\CivicTransparencyToolkit\README.txt" >nul 2>&1
    copy "LICENSE" "dist\CivicTransparencyToolkit\LICENSE" >nul 2>&1
    copy "Real World Example Sources List.csv" "dist\CivicTransparencyToolkit\Real World Example Sources List.csv" >nul 2>&1
    if exist "Civic Transparency Toolkit - User Guide.docx" (
        copy "Civic Transparency Toolkit - User Guide.docx" "dist\CivicTransparencyToolkit\Civic Transparency Toolkit - User Guide.docx" >nul 2>&1
        echo   Bundled user guide.
    )

    REM Bundle full source code so recipients can read, modify, and rebuild
    if exist "dist\CivicTransparencyToolkit\source" rmdir /s /q "dist\CivicTransparencyToolkit\source"
    mkdir "dist\CivicTransparencyToolkit\source"
    copy "*.py" "dist\CivicTransparencyToolkit\source\" >nul 2>&1
    copy "*.bat" "dist\CivicTransparencyToolkit\source\" >nul 2>&1
    copy "*.spec" "dist\CivicTransparencyToolkit\source\" >nul 2>&1
    copy "*.txt" "dist\CivicTransparencyToolkit\source\" >nul 2>&1
    copy "*.csv" "dist\CivicTransparencyToolkit\source\" >nul 2>&1
    copy "LICENSE" "dist\CivicTransparencyToolkit\source\" >nul 2>&1
    xcopy "prompts" "dist\CivicTransparencyToolkit\source\prompts\" /s /e /q >nul 2>&1
    xcopy "templates" "dist\CivicTransparencyToolkit\source\templates\" /s /e /q >nul 2>&1
    xcopy "assets" "dist\CivicTransparencyToolkit\source\assets\" /s /e /q >nul 2>&1
    echo.

    echo Step 5 of 6: Renaming to versioned folder...
    REM PyInstaller always outputs to dist\CivicTransparencyToolkit — rename to versioned name
    if exist "dist\CivicTransparencyToolkit-%VERSION%" rmdir /s /q "dist\CivicTransparencyToolkit-%VERSION%"
    rename "dist\CivicTransparencyToolkit" "CivicTransparencyToolkit-%VERSION%"
    echo   Created: dist\CivicTransparencyToolkit-%VERSION%\
    echo.

    echo Step 6 of 6: Creating zip for distribution...
    if exist "dist\CivicTransparencyToolkit-%VERSION%.zip" del "dist\CivicTransparencyToolkit-%VERSION%.zip"
    powershell -NoProfile -Command "Compress-Archive -Path 'dist\CivicTransparencyToolkit-%VERSION%' -DestinationPath 'dist\CivicTransparencyToolkit-%VERSION%.zip'"
    if exist "dist\CivicTransparencyToolkit-%VERSION%.zip" (
        echo   Created: dist\CivicTransparencyToolkit-%VERSION%.zip
    ) else (
        echo   WARNING: Zip creation failed. You can zip the folder manually.
    )
    echo.
    echo ============================================================
    echo  BUILD SUCCESSFUL — %VERSION%
    echo ============================================================
    echo.
    echo  Folder:  dist\CivicTransparencyToolkit-%VERSION%\
    echo  Zip:     dist\CivicTransparencyToolkit-%VERSION%.zip
    echo.
    echo  Previous builds in dist\ are preserved.
    echo  To distribute: share the .zip or copy the folder to USB.
    echo.
    REM Show all versions in dist
    echo  All versions in dist\:
    for /d %%d in (dist\CivicTransparencyToolkit-v*) do echo    %%~nxd
    echo.
) else (
    echo ============================================================
    echo BUILD FAILED
    echo ============================================================
    echo.
    echo Check the error messages above. Common fixes:
    echo   - Make sure Python 3.9+ is installed
    echo   - Try running: %PYTHON% -m pip install pyinstaller
    echo   - Then:        %PYTHON% -m PyInstaller --onedir --windowed main.py
)
echo.
pause
