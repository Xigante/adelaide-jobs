@echo off
setlocal
title adelaide-jobs - buscar vagas e abrir o relatorio

echo.
echo   =====================================================
echo     Buscar vagas novas e abrir o relatorio
echo   =====================================================
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

set "VENV=%USERPROFILE%\.venvs\adelaide-jobs"
set "VPY=%VENV%\Scripts\python.exe"
set "VAPP=%VENV%\Scripts\adelaide-jobs.exe"
if not exist "%VPY%" (
  echo   [ERRO] O ambiente ainda nao existe.
  echo   Rode o INSTALAR.bat uma vez antes deste aqui.
  goto FIM
)

echo   [..]   Atualizando o programa ^(o codigo mudou hoje^)...
"%VPY%" -m pip install -e ".[ats]" --quiet --upgrade
echo   [ok]   Atualizado.
echo.

echo   [..]   Buscando vagas. Demora de 3 a 6 minutos.
echo          Adzuna + ATS dos empregadores + SA Health.
echo.
"%VAPP%" collect
if errorlevel 1 goto ERRO_COLETA
echo.

echo   [..]   Recalculando as notas com os pesos novos...
"%VAPP%" score --rescore
echo.

echo   [..]   Gerando o relatorio...
"%VAPP%" export
echo.

echo   [..]   Atualizando a aba Empresas do material...
"%VPY%" "%~dp0aba-empresas.py"
echo.

echo   =====================================================
echo     Abrindo o relatorio no navegador
echo   =====================================================
echo.
if exist "%PROJ%\exports\vagas.html" (
  start "" "%PROJ%\exports\vagas.html"
  copy /y "%PROJ%\exports\vagas.html" "%PROJ%\exports\Vagas_Adelaide.html" >nul
  echo   Uma copia ficou tambem em:
  echo       %PROJ%\exports\Vagas_Adelaide.html
) else (
  echo   [ERRO] O relatorio nao foi gerado. Role a tela para cima.
)
echo.
echo   A planilha para o Excel:
echo       %PROJ%\exports\fila.csv
echo.
echo   Para ver todos os caminhos:  "%VAPP%" onde
echo.
goto FIM

:ERRO_COLETA
echo.
echo   [ERRO] A coleta falhou. Role a tela para cima e me mande
echo   a ultima mensagem de erro.
echo.

:FIM
pause
endlocal
