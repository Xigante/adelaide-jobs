@echo off
setlocal
title Enviar adelaide-jobs para o GitHub

REM  Chamado com o argumento 'encadeado' (pelo ATUALIZAR-VAGAS.bat),
REM  este script nao pausa no fim nem oferece a configuracao do Pages:
REM  quem chamou continua a conversa.
set "ENCADEADO=%~1"

echo.
echo   =====================================================
echo     Enviar para o GitHub
echo   =====================================================
echo.

where git >nul 2>&1
if errorlevel 1 goto SEM_GIT
for /f "delims=" %%v in ('git --version 2^>nul') do echo   [ok]   %%v

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
if not exist "%PROJ%\.git\HEAD" (
  echo   [ERRO] Nao achei o repositorio em:
  echo          %PROJ%
  goto FIM
)
cd /d "%PROJ%"
echo   [ok]   Projeto: %PROJ%
echo.

REM ---------------------------------------------------------------
REM  Arquivos .lock que o git deixa para tras travam tudo.
REM ---------------------------------------------------------------
if exist ".git\index.lock" del /f /q ".git\index.lock" >nul 2>&1
if exist ".git\HEAD.lock" del /f /q ".git\HEAD.lock" >nul 2>&1

REM ---------------------------------------------------------------
REM  Pasta de rebase VAZIA que ficou para tras trava todo pull.
REM  O git so olha se ela existe. No Windows com OneDrive, o
REM  'rebase --abort' apaga o conteudo mas as vezes nao a pasta,
REM  porque o OneDrive esta segurando ela.
REM  'rd' SEM /s so remove pasta vazia e falha se tiver algo dentro:
REM  e impossivel isto aqui destruir um rebase de verdade.
REM ---------------------------------------------------------------
rd /q ".git\rebase-merge" >nul 2>&1
rd /q ".git\rebase-apply" >nul 2>&1
if exist ".git\rebase-merge" echo   [!]    Rebase pela metade em .git\rebase-merge. Me mande esta tela.
if exist ".git\rebase-apply" echo   [!]    Rebase pela metade em .git\rebase-apply. Me mande esta tela.

REM ---------------------------------------------------------------
REM  O Git Credential Manager abre o navegador para voce entrar.
REM  Sem token para colar, sem token para vazar.
REM ---------------------------------------------------------------
git config --local credential.helper manager >nul 2>&1
git config --local core.filemode false >nul 2>&1

REM ---------------------------------------------------------------
REM  O material muda a cada coleta. Publicar a copia do /docs e
REM  fechar o commit tem que acontecer AQUI: se ficar por conta de
REM  lembrar, a pagina do celular congela na versao de duas semanas
REM  atras enquanto o material no PC segue novo. Ja aconteceu.
REM ---------------------------------------------------------------
set "VPY=%USERPROFILE%\.venvs\adelaide-jobs\Scripts\python.exe"
if not exist "%VPY%" set "VPY=python"

echo   [..]   Publicando o material na pasta docs...
"%VPY%" "%~dp0publicar-no-github-pages.py"
if errorlevel 1 (
  echo   [ERRO] Nao consegui gerar a pagina do celular.
  echo   Rode o ATUALIZAR-VAGAS.bat primeiro e tente de novo.
  goto FIM
)
echo.

echo   [..]   Guardando o que mudou...
git add -A
git --no-pager diff --cached --stat
git diff --cached --quiet
if errorlevel 1 (
  git commit -q -m "Coleta de %DATE%: vagas, empresas e pagina do celular"
  echo   [ok]   Commit criado.
) else (
  echo   [ok]   Nada novo para guardar.
)
echo.

REM ---------------------------------------------------------------
REM  Sao dois computadores agora. Quem enviou por ultimo deixa o
REM  GitHub na frente do outro, e o push do outro morre com
REM  'fetch first'. Trazer antes de mandar resolve isso sozinho.
REM  --rebase poe o que voce fez aqui EM CIMA do que ja estava la,
REM  sem commit de juncao e sem perder nada.
REM ---------------------------------------------------------------
echo   [..]   Trazendo o que mudou no GitHub...
git pull --rebase origin main
if errorlevel 1 goto ERRO_PULL
echo   [ok]   Em dia com o GitHub.
echo.

echo   ---------------------------------------------------
echo    Commits que vao subir:
echo   ---------------------------------------------------
git --no-pager log --oneline origin/main..HEAD
echo.

echo   [..]   Enviando...
echo.
echo          Se abrir uma janela do navegador pedindo login
echo          do GitHub, entre normalmente e volte para ca.
echo.
git push origin main
if errorlevel 1 goto ERRO_PUSH

echo.
echo   =====================================================
echo     Enviado.
echo   =====================================================
echo.
echo   A pagina do celular leva ate 2 minutos para atualizar:
echo       https://xigante.github.io/adelaide-jobs/
echo.
if /i "%ENCADEADO%"=="encadeado" goto FIM
echo   ---------------------------------------------------
echo   Se a pagina der 404, e porque o GitHub Pages ainda
echo   nao foi ligado. Isso se faz UMA VEZ SO:
echo.
echo     1. https://github.com/Xigante/adelaide-jobs/settings/pages
echo     2. Em "Source" escolha: Deploy from a branch
echo     3. Branch: main    Pasta: /docs    e clique em Save
echo.
echo   Se a pagina ja abre normalmente, ignore isto.
echo.
choice /c SN /n /m "  Abrir a configuracao do Pages? (S/N) "
if errorlevel 2 goto FIM
start "" "https://github.com/Xigante/adelaide-jobs/settings/pages"
goto FIM

:ERRO_PULL
echo.
echo   [ERRO] Nao consegui juntar o que esta no GitHub com o que
echo          esta neste computador.
echo.
git rebase --abort >nul 2>&1
rd /q ".git\rebase-merge" >nul 2>&1
echo   Desfiz a juncao pela metade. NADA foi perdido: o seu trabalho
echo   continua aqui, do jeito que estava antes de eu tentar.
echo.
echo   Isso acontece quando o MESMO arquivo mudou nos dois
echo   computadores. Copie as linhas acima e me mande.
goto FIM

:ERRO_PUSH
echo.
echo   [ERRO] O envio falhou.
echo.
echo   As duas causas comuns:
echo.
echo   1. Login recusado. Rode este comando e tente de novo:
echo        git credential-manager github login
echo.
echo   2. O GitHub esta na frente deste computador. Este botao ja
echo      tenta resolver sozinho antes de enviar, entao se voce
echo      chegou aqui e outra coisa. Me mande a mensagem.
echo.
echo   Copie a mensagem de erro acima e me mande.
goto FIM

:SEM_GIT
echo   [ERRO] O Git nao esta instalado.
echo   Baixe em https://git-scm.com/download/win
echo   Na instalacao pode aceitar tudo que ja vem marcado.
echo.
choice /c SN /n /m "  Abrir a pagina de download? (S/N) "
if errorlevel 2 goto FIM
start "" "https://git-scm.com/download/win"

:FIM
echo.
if /i not "%ENCADEADO%"=="encadeado" pause
endlocal
