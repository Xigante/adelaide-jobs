@echo off
setlocal
title Enviar adelaide-jobs para o GitHub

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
echo   Agora falta LIGAR a pagina, uma vez so:
echo.
echo     1. Abra:
echo        https://github.com/Xigante/adelaide-jobs/settings/pages
echo     2. Em "Source" escolha: Deploy from a branch
echo     3. Branch: main    Pasta: /docs
echo     4. Clique em Save
echo     5. Espere 2 minutos e abra:
echo        https://xigante.github.io/adelaide-jobs/
echo.
choice /c SN /n /m "  Abrir a pagina de configuracao agora? (S/N) "
if errorlevel 2 goto FIM
start "" "https://github.com/Xigante/adelaide-jobs/settings/pages"
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
echo   2. Alguem mudou o repositorio no site. Rode:
echo        git pull --rebase origin main
echo      e depois este .bat outra vez.
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
pause
endlocal
