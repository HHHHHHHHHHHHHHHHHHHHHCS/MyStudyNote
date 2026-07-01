@echo off
chcp 65001 >nul

echo ============================================
echo   Build TestProjectEditor (Win64 Development)
echo ============================================
echo.

REM To build the Game target, change TestProjectEditor below to TestProject.
call E:\UnrealEngine\Engine\Build\BatchFiles\Build.bat ^
    TestProjectEditor Win64 Development ^
    "F:\TestProject\TestProject.uproject" ^
    -Progress ^
    -NoHotReload

echo.
if %ERRORLEVEL% EQU 0 (
    echo Build SUCCESS!
) else (
    echo Build FAILED with error code: %ERRORLEVEL%
)
