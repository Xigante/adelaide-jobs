@echo off
setlocal EnableExtensions
title adelaide-jobs - instalar neste computador

echo.
echo   ============================================================
echo     adelaide-jobs - instalacao
echo   ============================================================
echo.
echo   Isto monta tudo neste computador. Demora de 2 a 5 minutos, e
echo   voce so precisa rodar UMA VEZ por computador.
echo.
echo   No fim voce vai ter tres botoes:
echo     - Atualizar vagas    busca vagas novas e abre o relatorio
echo     - Enviar para GitHub sobe as melhorias
echo     - Reparar banco      conserta o banco se ele quebrar
echo.
pause
echo.

REM ---------------------------------------------------------------
REM  0. Onde estamos
REM ---------------------------------------------------------------
set "PROJ=%~dp0"
if "%PROJ:~-1%"=="\" set "PROJ=%PROJ:~0,-1%"
if not exist "%PROJ%\pyproject.toml" (
  echo   [ERRO] Este arquivo precisa ficar na raiz do projeto, ao lado
  echo          do pyproject.toml. Ele esta em:
  echo          %PROJ%
  goto FIM
)
cd /d "%PROJ%"
echo   [ok]   Projeto: %PROJ%

REM ---------------------------------------------------------------
REM  1. Python
REM ---------------------------------------------------------------
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY python --version >nul 2>&1 && set "PY=python"
if not defined PY goto SEM_PYTHON
for /f "delims=" %%v in ('%PY% --version 2^>^&1') do echo   [ok]   %%v

REM ---------------------------------------------------------------
REM  2. Ambiente virtual, FORA de qualquer pasta sincronizada
REM     Um virtualenv tem milhares de arquivos pequenos e o OneDrive
REM     tenta sincronizar todos. Por isso ele mora no perfil.
REM ---------------------------------------------------------------
set "VENV=%USERPROFILE%\.venvs\adelaide-jobs"
set "VPY=%VENV%\Scripts\python.exe"
if exist "%VPY%" (
  echo   [ok]   Ambiente ja existe: %VENV%
) else (
  echo   [..]   Criando o ambiente em %VENV%
  %PY% -m venv "%VENV%"
  if not exist "%VPY%" (
    echo   [ERRO] Nao consegui criar o ambiente.
    echo          Rode este arquivo de novo. Se insistir, me mande a tela.
    goto FIM
  )
  echo   [ok]   Ambiente criado.
)

echo   [..]   Instalando o programa. Esta e a parte demorada.
"%VPY%" -m pip install --upgrade pip --quiet
"%VPY%" -m pip install -e ".[ats]" --quiet
if errorlevel 1 (
  echo   [ERRO] A instalacao falhou. Role a tela para cima: quase sempre
  echo          e falta de internet ou um antivirus barrando o pip.
  goto FIM
)
echo   [ok]   Programa instalado.

REM ---------------------------------------------------------------
REM  3. As chaves da Adzuna
REM     Elas ficam so no .env, que o git ignora. Quem digita e voce:
REM     nao passe essas chaves por chat, e-mail nem print.
REM ---------------------------------------------------------------
echo.
if exist "%PROJ%\.env" (
  echo   [ok]   O arquivo .env ja existe.
) else (
  copy /y "%PROJ%\.env.example" "%PROJ%\.env" >nul
  echo   ============================================================
  echo     Falta so a chave da Adzuna
  echo   ============================================================
  echo.
  echo   1. Abra  https://developer.adzuna.com/  e crie uma conta.
  echo      E gratis e a chave sai na hora.
  echo   2. Vou abrir o Bloco de Notas. Cole o app_id e o app_key nas
  echo      linhas ADZUNA_APP_ID e ADZUNA_APP_KEY.
  echo   3. Salve e feche o Bloco de Notas para continuar.
  echo.
  pause
  notepad "%PROJ%\.env"
)

REM ---------------------------------------------------------------
REM  4. Conferir
REM ---------------------------------------------------------------
echo.
echo   [..]   Conferindo a instalacao...
"%VENV%\Scripts\adelaide-jobs.exe" doctor
echo.

REM ---------------------------------------------------------------
REM  5. O botao de play
REM ---------------------------------------------------------------
echo   ============================================================
echo     Quer um atalho na area de trabalho?
echo   ============================================================
echo.
set "R="
set /p "R=  Digite S para sim, ou so aperte Enter para pular: "
if /i "%R%"=="S" call "%PROJ%\ferramentas\CRIAR-ATALHO.bat"

REM ---------------------------------------------------------------
echo.
echo   ============================================================
echo     Pronto. Daqui para frente e so isto:
echo   ============================================================
echo.
echo     ferramentas\ATUALIZAR-VAGAS.bat     todo dia, uma vez
echo     ferramentas\ENVIAR-PARA-GITHUB.bat  quando quiser publicar
echo     ferramentas\REPARAR-BANCO.bat       so se der erro no banco
echo.
echo   Como usar cada detalhe:  docs\como-funciona.html
echo   O que dizer para uma IA: PROMPT-PARA-IA.md
echo.
goto FIM

:SEM_PYTHON
echo.
echo   [ERRO] Nao achei Python neste computador.
echo.
echo   Instale de um destes jeitos e rode este arquivo de novo:
echo.
echo     a^) No menu Iniciar, abra o "Terminal" e cole:
echo            winget install Python.Python.3.12
echo.
echo     b^) Ou baixe em  https://www.python.org/downloads/
echo        MARQUE a caixa "Add python.exe to PATH" na primeira tela.
echo.

:FIM
echo.
pause
endlocal
