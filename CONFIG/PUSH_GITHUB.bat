@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title IndieStudio — GitHub Sync

echo.
echo ================================================
echo   IndieStudio GitHub Sync
echo ================================================
echo.

:: ---- Leer usuario y token (usebackq = leer desde archivo, no como string) ----
set TOKEN_FILE=%~dp0.github_token
if not exist "!TOKEN_FILE!" (
    echo [ERROR] No encontre .github_token en CONFIG\
    echo         Formato:  Brunich:TU_TOKEN
    pause & exit /b 1
)

for /f "usebackq tokens=1* delims=:" %%a in ("!TOKEN_FILE!") do (
    set GH_USER=%%a
    set GH_TOKEN=%%b
)

echo [OK] Usuario: !GH_USER!

:: ---- Registrar repos como seguros (arregla error "dubious ownership") ----
echo [i] Configurando safe.directory...
git config --global --add safe.directory "C:/Users/bruni/OneDrive/Desktop/Programming Brunich/IA TEAM"
git config --global --add safe.directory "C:/Users/bruni/OneDrive/Desktop/Apps/GODOT/godot-modular-arc-demo-master"

:: ===================================================
:: REPO 1: Indie-Junior-Projects
:: ===================================================
echo.
echo --- Repo 1: Indie-Junior-Projects ---
set REPO1=%~dp0..
cd /d "!REPO1!"

set URL1=https://!GH_USER!:!GH_TOKEN!@github.com/Brunich/Indie-Junior-Projects.git
git remote remove origin 2>nul
git remote add origin "!URL1!"

:: Commitear si hay cambios
git status --porcelain > "%TEMP%\gs1.txt" 2>nul
set EMPTY1=1
for /f "usebackq" %%i in ("%TEMP%\gs1.txt") do set EMPTY1=0
if !EMPTY1!==0 (
    git add -A
    git commit -m "Auto-sync %DATE% — agentes Cowork"
    echo [+] Commit creado
) else (
    echo [i] Sin cambios nuevos
)

git push -u origin main --force 2>&1
if !errorlevel!==0 (
    echo [OK] Indie-Junior-Projects actualizado en GitHub
) else (
    echo [!] Fallo. Crea el repo vacio en: https://github.com/new ^> Indie-Junior-Projects
)

:: ===================================================
:: REPO 2: godot-modular-arc-demo
:: ===================================================
echo.
echo --- Repo 2: godot-modular-arc-demo ---
set REPO2=C:\Users\bruni\OneDrive\Desktop\Apps\GODOT\godot-modular-arc-demo-master

if not exist "!REPO2!" (
    echo [!] No encontre la carpeta del proyecto Godot
    goto :final
)

cd /d "!REPO2!"

set URL2=https://!GH_USER!:!GH_TOKEN!@github.com/Brunich/godot-modular-arc-demo.git
git remote remove origin 2>nul
git remote add origin "!URL2!"

:: Commitear si hay cambios
git status --porcelain > "%TEMP%\gs2.txt" 2>nul
set EMPTY2=1
for /f "usebackq" %%i in ("%TEMP%\gs2.txt") do set EMPTY2=0
if !EMPTY2!==0 (
    git add -A
    git commit -m "Mejoras Bruno %DATE%"
    echo [+] Commit en godot-modular-arc-demo
) else (
    echo [i] Sin cambios nuevos
)

git push -u origin main --force 2>&1
if !errorlevel!==0 (
    echo [OK] godot-modular-arc-demo actualizado en GitHub
) else (
    echo [!] Fallo. Crea el repo vacio en: https://github.com/new ^> godot-modular-arc-demo
)

:final
echo.
echo ================================================
echo   Sync completado — https://github.com/Brunich
echo ================================================
echo.
pause
