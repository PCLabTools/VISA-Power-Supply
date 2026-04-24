@echo off
setlocal EnableExtensions

for %%I in ("%~dp0..") do set "REPO_ROOT=%%~fI"
cd /d "%REPO_ROOT%"

set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

:menu
cls
echo ======================================
echo PAF Template Project Build Menu
echo ======================================
echo.
echo   1. Build Windows executable
echo   2. Build Linux executable
echo   3. Build both executables
echo   4. Exit
echo.
set /p "BUILD_CHOICE=Select an option [1-4]: "

if "%BUILD_CHOICE%"=="1" goto build_windows
if "%BUILD_CHOICE%"=="2" goto build_linux
if "%BUILD_CHOICE%"=="3" goto build_both
if "%BUILD_CHOICE%"=="4" goto end

echo.
echo Invalid selection.
pause
goto menu

:build_windows
echo.
echo Running Windows build...
"%PYTHON_EXE%" "%REPO_ROOT%\scripts\build-windows.py"
set "BUILD_EXIT_CODE=%ERRORLEVEL%"
goto report_result

:build_linux
echo.
echo Running Linux build...
"%PYTHON_EXE%" "%REPO_ROOT%\scripts\build-linux.py"
set "BUILD_EXIT_CODE=%ERRORLEVEL%"
goto report_result

:build_both
echo.
echo Running Windows build...
"%PYTHON_EXE%" "%REPO_ROOT%\scripts\build-windows.py"
if errorlevel 1 (
    set "BUILD_EXIT_CODE=%ERRORLEVEL%"
    goto report_result
)

echo.
echo Running Linux build...
"%PYTHON_EXE%" "%REPO_ROOT%\scripts\build-linux.py"
set "BUILD_EXIT_CODE=%ERRORLEVEL%"
goto report_result

:report_result
echo.
if "%BUILD_EXIT_CODE%"=="0" (
    echo Build completed successfully.
) else (
    echo Build failed with exit code %BUILD_EXIT_CODE%.
)
echo.
pause
goto menu

:end
exit /b 0