@echo off
setlocal EnableExtensions
title adelaide-jobs - testar a caixa de alertas

echo.
echo   ============================================================
echo     Testar a caixa de alertas de e-mail
echo   ============================================================
echo.
echo   Conecta na caixa, olha o que tem la dentro e sai. Dois
echo   segundos. Nao coleta nada e nao gasta cota de API nenhuma.
echo.

rem  Acha a pasta do projeto a partir deste arquivo: ao lado do
rem  pyproject.toml, uma pasta acima, ou dentro de adelaide-jobs\.
set "AQUI=%~dp0"
set "PROJ="
if exist "%AQUI%pyproject.toml" for %%I in ("%AQUI%.") do set "PROJ=%%~fI"
if not defined PROJ if exist "%AQUI%..\pyproject.toml" for %%I in ("%AQUI%..") do set "PROJ=%%~fI"
if not defined PROJ if exist "%AQUI%adelaide-jobs\pyproject.toml" for %%I in ("%AQUI%adelaide-jobs") do set "PROJ=%%~fI"
if not defined PROJ (
  echo   [ERRO] Nao achei o pyproject.toml a partir de:
  echo          %AQUI%
  goto FIM
)
cd /d "%PROJ%"

set "VPY=%USERPROFILE%\.venvs\adelaide-jobs\Scripts\python.exe"
if not exist "%VPY%" set "VPY=py"
if not exist "%USERPROFILE%\.venvs\adelaide-jobs\Scripts\python.exe" where py >nul 2>nul || set "VPY=python"

"%VPY%" "%~dp0testar_email.py"

:FIM
echo.
pause
endlocal
