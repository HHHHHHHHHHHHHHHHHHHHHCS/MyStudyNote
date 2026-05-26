---
name: vs-build-tools
description: Preferred local Visual Studio 2022 Community installation and build tool discovery rules for this Windows machine. Use when Codex needs to compile C/C++ projects, invoke MSBuild, locate MSVC CL.exe, set up the Visual Studio developer environment, or diagnose build commands that depend on Microsoft Visual Studio compiler tools.
---

# VS Build Tools

Prefer the Visual Studio 2022 Community installation under `D:\Microsoft Visual Studio\2022\Community` when a task needs Microsoft build tools on this machine. Treat this directory as the preferred VS root, not as a guarantee that every nested version-specific executable path is permanent.

## Preferred VS Root

Use this root first:

```text
D:\Microsoft Visual Studio\2022\Community
```

If an instruction or note contains `:\Microsoft Visual Studio\...`, treat it as missing the `D:` drive prefix unless the user says otherwise.

## Preferred Tool Paths

- MSBuild:
  `D:\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe`
- Developer environment:
  `D:\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat`
- VC environment shortcut:
  `D:\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat`

## CL.exe Discovery

Do not treat the MSVC version folder as fixed. The currently known compiler path is:

```text
D:\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.38.33130\bin\HostX86\x64\CL.exe
```

Use that path only as a current known location or for diagnostics. For new build commands, prefer initializing the Visual Studio environment and calling `cl`.

When a specific `CL.exe` path is required, discover the newest installed MSVC version under:

```text
D:\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC
```

PowerShell discovery example:

```powershell
$msvcRoot = 'D:\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC'
$cl = Get-ChildItem -LiteralPath $msvcRoot -Directory |
    Sort-Object Name -Descending |
    ForEach-Object { Join-Path $_.FullName 'bin\HostX86\x64\CL.exe' } |
    Where-Object { Test-Path -LiteralPath $_ } |
    Select-Object -First 1
```

## Usage

Prefer full quoted paths because the Visual Studio install directory contains spaces.

PowerShell example for MSBuild:

```powershell
& 'D:\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe' .\Project.sln /m /p:Configuration=Debug /p:Platform=x64
```

For direct `CL.exe` usage, initialize the Visual Studio environment first so `INCLUDE`, `LIB`, `LIBPATH`, Windows SDK paths, and MSVC tool paths are available.

PowerShell example:

```powershell
cmd /c '"D:\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" && cl /?'
```

Use the explicit `CL.exe` path only when a task specifically needs to locate the binary. For real compilation commands, prefer calling `cl` after `vcvars64.bat` or `VsDevCmd.bat` has been loaded.

## Validation

Before relying on these paths in a build fix, check that the preferred VS root and needed tool files still exist with `Test-Path -LiteralPath '<path>'`. If a nested tool path is missing, search under `D:\Microsoft Visual Studio\2022\Community` before assuming Visual Studio is unavailable.
