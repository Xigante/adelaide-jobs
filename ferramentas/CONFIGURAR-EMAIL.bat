@echo off
setlocal
title adelaide-jobs - configurar a caixa de alertas

echo.
echo   =====================================================
echo     Configurar o e-mail dos alertas
echo   =====================================================
echo.
echo   Voce vai precisar de duas coisas na mao:
echo.
echo     1. O endereco da conta NOVA do Gmail
echo     2. A senha de app de 16 caracteres (a "coletor-vagas")
echo.
echo   Se ainda nao criou a senha de app, feche esta janela e
echo   abra:  https://myaccount.google.com/apppasswords
echo.
pause
echo.

rem  Acha a pasta do projeto a partir deste arquivo.
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

"%VPY%" "%~dp0configurar_email.py"
if errorlevel 1 goto FIM

echo   ---------------------------------------------------
echo    Testar a conexao agora?
echo   ---------------------------------------------------
echo.
echo   O teste conecta na caixa e mostra o que achou. Nao
echo   gasta cota de API nenhuma.
echo.
echo   ATENCAO: se voce assinou os alertas hoje, eles so
echo   chegam amanha de manha. O teste vai dizer que a caixa
echo   esta vazia, e isso e o esperado - o importante hoje e
echo   ver a frase "conectado" e nenhum erro de senha.
echo.
choice /c SN /n /m "  Testar agora? (S/N) "
if errorlevel 2 goto FIM
echo.
"%VPY%" "%~dp0testar_email.py"

:FIM
echo.
pause
endlocal
