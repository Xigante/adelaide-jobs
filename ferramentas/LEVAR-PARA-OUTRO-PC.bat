@echo off
setlocal
title adelaide-jobs - levar para outro computador

REM ---------------------------------------------------------------
REM  Migalhas num arquivo. A janela do cmd some quando o script
REM  morre cedo, e ai nao sobra nada para diagnosticar. Cada ponto
REM  do caminho escreve aqui, entao o ultimo que aparecer no log e
REM  onde parou.
REM ---------------------------------------------------------------
set "LOG=%~dp0_ultima-execucao.txt"
> "%LOG%" echo [1] iniciado  %DATE% %TIME%

echo.
echo   =====================================================
echo     Levar para outro computador
echo   =====================================================
echo.
echo   O GitHub leva o programa inteiro. Duas coisas ficam
echo   de fora e sao justamente as que doem:
echo.
echo     .env      as chaves (Adzuna e senha de app do Gmail)
echo     jobs.db   o historico inteiro da coleta
echo.
echo   Este botao junta as duas num zip, com um LEIA-ME do
echo   passo a passo no computador novo.
echo.
pause
echo.

>> "%LOG%" echo [2] passou do primeiro pause
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
>> "%LOG%" echo [3] projeto: %PROJ%
cd /d "%PROJ%"

set "VPY=%USERPROFILE%\.venvs\adelaide-jobs\Scripts\python.exe"
if not exist "%VPY%" set "VPY=python"
>> "%LOG%" echo [4] python: %VPY%
"%VPY%" "%~dp0levar_para_outro_pc.py"
>> "%LOG%" echo [5] python terminou com codigo %ERRORLEVEL%
if errorlevel 1 goto FIM

echo   ---------------------------------------------------
choice /c SN /n /m "  Abrir a pasta onde o zip ficou? (S/N) "
if errorlevel 2 goto FIM
for %%I in ("%PROJ%\..") do start "" "%%~fI"

:FIM
>> "%LOG%" echo [6] chegou no fim
echo.
echo   Se algo deu errado, o registro do que aconteceu esta em:
echo       %LOG%
echo.
pause
endlocal
