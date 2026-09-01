@echo off
setlocal
title adelaide-jobs - reparar o banco de vagas

echo.
echo   =====================================================
echo     Reparar o banco de vagas
echo   =====================================================
echo.
echo   Use isto quando a coleta morrer com a mensagem
echo   "database disk image is malformed".
echo.
echo   Ele NAO apaga nada: o banco de antes fica guardado ao
echo   lado, com a data no nome.
echo.

rem  Acha a pasta do projeto a partir deste arquivo: ao lado do
rem  pyproject.toml, uma pasta acima, ou dentro de adelaide-jobs\.
rem  Assim o mesmo .bat funciona em ferramentas\ e solto na pasta de cima.
set "AQUI=%~dp0"
set "PROJ="
if exist "%AQUI%pyproject.toml" for %%I in ("%AQUI%.") do set "PROJ=%%~fI"
if not defined PROJ if exist "%AQUI%..\pyproject.toml" for %%I in ("%AQUI%..") do set "PROJ=%%~fI"
if not defined PROJ if exist "%AQUI%adelaide-jobs\pyproject.toml" for %%I in ("%AQUI%adelaide-jobs") do set "PROJ=%%~fI"
if not defined PROJ (
  echo   [ERRO] Nao achei o pyproject.toml a partir de:
  echo          %AQUI%
  echo   Este arquivo precisa estar dentro da pasta do projeto.
  goto FIM
)
cd /d "%PROJ%"
if not exist "%~dp0reparar_banco.py" (
  echo   [ERRO] Nao achei reparar_banco.py ao lado deste arquivo.
  goto FIM
)

set "VPY=%USERPROFILE%\.venvs\adelaide-jobs\Scripts\python.exe"
if exist "%VPY%" goto RODA
set "VPY=py"
where py >nul 2>nul && goto RODA
set "VPY=python"
where python >nul 2>nul && goto RODA
echo   [ERRO] Nao achei nenhum Python nesta maquina.
echo   Rode o INSTALAR.bat primeiro.
goto FIM

:RODA
"%VPY%" "%~dp0reparar_banco.py"

:FIM
echo.
pause
endlocal
