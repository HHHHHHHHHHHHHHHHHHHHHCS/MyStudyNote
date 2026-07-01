@echo off
setlocal

rem === Required config ===
rem Paks directory that contains .pak and optional sidecar .json files.
set "UEPAK_INPUT_DIR=D:\MyGame\Content\Paks"

rem CSV output path.
set "UEPAK_OUTPUT_CSV=%~dp0PakInventory.csv"

rem Summary JSON output path.
set "UEPAK_SUMMARY_JSON=%~dp0PakInventory.summary.json"

rem Optional: UnrealPak.exe path. Only required when enabling fallback.
set "UEPAK_UNREALPAK=D:\MyEngine\Engine\Binaries\Win64\UnrealPak.exe"

rem Optional: Crypto.json path for encrypted pak indexes when using UnrealPak fallback.
set "UEPAK_CRYPTO_KEYS="

rem === Optional switches ===
set "UEPAK_PAK_PATTERN=*.pak"
set "UEPAK_MIN_SIZE_BYTES=0"
set "UEPAK_INCLUDE_EXTRA_FIELDS=0"
set "UEPAK_USE_UNREALPAK_FALLBACK=0"
set "UEPAK_QUIET=0"

if "%UEPAK_INPUT_DIR%"=="" (
    echo Please edit %~nx0 and set UEPAK_INPUT_DIR.
    exit /b 2
)

set "UEPAK_EXTRA_SWITCHES="

if "%UEPAK_INCLUDE_EXTRA_FIELDS%"=="1" (
    set "UEPAK_EXTRA_SWITCHES=%UEPAK_EXTRA_SWITCHES% --include-extra-fields"
)

if "%UEPAK_USE_UNREALPAK_FALLBACK%"=="1" (
    set "UEPAK_EXTRA_SWITCHES=%UEPAK_EXTRA_SWITCHES% --use-unrealpak-fallback"
)

if "%UEPAK_QUIET%"=="1" (
    set "UEPAK_EXTRA_SWITCHES=%UEPAK_EXTRA_SWITCHES% --quiet"
)

python "%~dp0UEPakReader.py" ^
    --input-dir "%UEPAK_INPUT_DIR%" ^
    --output-csv "%UEPAK_OUTPUT_CSV%" ^
    --summary-json "%UEPAK_SUMMARY_JSON%" ^
    --pak-pattern "%UEPAK_PAK_PATTERN%" ^
    --min-size-bytes "%UEPAK_MIN_SIZE_BYTES%" ^
    --unrealpak "%UEPAK_UNREALPAK%" ^
    --crypto-keys "%UEPAK_CRYPTO_KEYS%" ^
    %UEPAK_EXTRA_SWITCHES% %*
exit /b %ERRORLEVEL%
