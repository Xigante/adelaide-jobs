@echo off
setlocal
title adelaide-jobs - diagnosticar os alertas de e-mail

echo.
echo   =====================================================
echo     Diagnostico dos alertas
echo   =====================================================
echo.
echo   Abre os 12 e-mails mais recentes e mostra o FORMATO
echo   dos links que tem dentro, para descobrir por que uma
echo   plataforma nao esta sendo lida.
echo.
echo   Nao mostra o corpo dos e-mails nem nada pessoal:
echo   so remetente, assunto e os links das vagas.
echo.

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
if not exist "%VPY%" set "VPY=python"
"%VPY%" "%~dp0diagnosticar_email.py"

:FIM
echo.
pause
endlocal
