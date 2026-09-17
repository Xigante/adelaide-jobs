@echo off
setlocal
title Consertar e enviar - adelaide-jobs

REM ===================================================================
REM  Botao de uso UNICO, de 17/09/2026.
REM
REM  O que aconteceu: um 'git pull --rebase' comecou, trocou para o
REM  commit do GitHub e morreu no meio porque o OneDrive estava
REM  segurando arquivos da pasta. O git ficou SOLTO fora do ramo main
REM  ("detached HEAD"), e sobrou um .git\index.lock travando tudo.
REM
REM  Nada se perdeu: o ramo main continua apontando para todo o
REM  trabalho. Este arquivo so recoloca o git no lugar e envia.
REM
REM  Depois que der certo, pode apagar este arquivo.
REM ===================================================================

echo.
echo   =====================================================
echo     Consertar e enviar
echo   =====================================================
echo.

where git >nul 2>&1
if errorlevel 1 goto SEM_GIT

set "AQUI=%~dp0"
set "PROJ="
if exist "%AQUI%pyproject.toml" for %%I in ("%AQUI%.") do set "PROJ=%%~fI"
if not defined PROJ if exist "%AQUI%..\pyproject.toml" for %%I in ("%AQUI%..") do set "PROJ=%%~fI"
if not defined PROJ (
  echo   [ERRO] Nao achei o pyproject.toml a partir de:
  echo          %AQUI%
  goto FIM
)
cd /d "%PROJ%"
echo   [ok]   Projeto: %PROJ%
echo.

REM -------------------------------------------------------------------
REM  1. O cadeado que trava todo comando
REM -------------------------------------------------------------------
echo   [..]   Passo 1 de 4: tirando o cadeado do git...
if not exist ".git\index.lock" echo   [ok]   Nao tinha cadeado.
if exist ".git\index.lock" del /f /q ".git\index.lock" >nul 2>&1
if exist ".git\index.lock" powershell -NoProfile -Command "Remove-Item -LiteralPath '.git\index.lock' -Force -ErrorAction SilentlyContinue" >nul 2>&1
if exist ".git\index.lock" goto CADEADO_PRESO
echo   [ok]   Cadeado tirado.
echo.

REM -------------------------------------------------------------------
REM  2. Voltar para o ramo main
REM     -f porque a arvore ficou pela metade quando o rebase morreu:
REM     parte dela e do commit do GitHub, parte e do seu. O main tem a
REM     versao boa de tudo, entao mando o disco voltar a ser o main.
REM -------------------------------------------------------------------
echo   [..]   Passo 2 de 4: voltando para o ramo main...
git symbolic-ref -q HEAD >nul 2>&1
if not errorlevel 1 echo   [ok]   Ja estava no ramo certo.
git checkout -f main
if errorlevel 1 goto ERRO_CHECKOUT
for /f "delims=" %%B in ('git rev-parse --abbrev-ref HEAD') do set "RAMO=%%B"
echo   [ok]   No ramo: %RAMO%
echo.

REM -------------------------------------------------------------------
REM  3. Juntar o que veio do PC antigo. Merge, nao rebase: o rebase e
REM     justamente o que quebrou, e o merge nao usa aquela maquina.
REM -------------------------------------------------------------------
echo   [..]   Passo 3 de 4: juntando com o GitHub...
git fetch origin main
if errorlevel 1 goto ERRO_REDE
git merge origin/main --no-edit
if errorlevel 1 goto ERRO_MERGE
echo   [ok]   Juntado.
echo.

REM -------------------------------------------------------------------
REM  4. Enviar
REM -------------------------------------------------------------------
echo   ---------------------------------------------------
echo    Commits que vao subir:
echo   ---------------------------------------------------
git --no-pager log --oneline origin/main..HEAD
echo.
echo   [..]   Passo 4 de 4: enviando...
echo.
echo          Se abrir o navegador pedindo login do GitHub,
echo          entre normalmente e volte para ca.
echo.
git push origin main
if errorlevel 1 goto ERRO_PUSH

echo.
echo   =====================================================
echo     Pronto. Esta tudo no GitHub.
echo   =====================================================
echo.
echo   Daqui para frente use o ENVIAR-PARA-GITHUB.bat de sempre.
echo   Pode apagar este arquivo.
echo.
goto FIM

:CADEADO_PRESO
echo.
echo   [ERRO] Nao consegui apagar o .git\index.lock.
echo.
echo   Alguma coisa ainda esta segurando esse arquivo: ou o
echo   OneDrive, ou um git que ficou rodando de uma janela que
echo   voce fechou no meio.
echo.
echo   O conserto e: REINICIE o computador, pause o OneDrive,
echo   e rode este arquivo outra vez. Nada se perde nisso.
goto FIM

:ERRO_CHECKOUT
echo.
echo   [ERRO] Nao consegui voltar para o ramo main.
echo          Seu trabalho continua salvo. Me mande esta tela.
goto FIM

:ERRO_REDE
echo.
echo   [ERRO] Nao consegui falar com o GitHub.
echo          Confira a internet e tente de novo.
goto FIM

:ERRO_MERGE
echo.
echo   [ERRO] O mesmo arquivo mudou nos dois computadores e o git
echo          nao soube escolher. Nada foi perdido.
echo.
echo   Rode isto para voltar ao ponto de partida:
echo        git merge --abort
echo   e me mande esta tela.
goto FIM

:ERRO_PUSH
echo.
echo   [ERRO] O envio falhou, mas o conserto funcionou: o git ja
echo          esta no ramo certo e em dia com o GitHub.
echo.
echo   Se falou em login, rode:
echo        git credential-manager github login
echo   e rode este arquivo outra vez.
echo.
echo   Copie a mensagem acima e me mande.
goto FIM

:SEM_GIT
echo   [ERRO] O Git nao esta instalado.
echo   Baixe em https://git-scm.com/download/win

:FIM
echo.
pause
endlocal
