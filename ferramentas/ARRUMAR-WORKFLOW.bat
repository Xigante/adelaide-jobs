@echo off
setlocal
title Arrumar o workflow - adelaide-jobs

REM ===================================================================
REM  Botao de uso UNICO, de 21/09/2026.
REM
REM  O arquivo do workflow subiu para o GitHub como
REM      github/workflows/coleta-diaria.yml     (sem o ponto)
REM  e o GitHub Actions so le de
REM      .github/workflows/coleta-diaria.yml    (com o ponto).
REM
REM  Sem o ponto ele e um texto qualquer e nada roda.
REM
REM  O conteudo do arquivo esta certo, conferido linha a linha. Falta
REM  so o nome da pasta. O Explorer do Windows nao cria pasta comecando
REM  com ponto; o git cria. Por isso isto aqui e um .bat e nao um
REM  arrastar-e-soltar.
REM
REM  Depois que der certo, pode apagar este arquivo.
REM ===================================================================

echo.
echo   =====================================================
echo     Arrumar o workflow
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

REM  A mesma limpeza do botao de enviar: cadeado e rebase vazio.
if exist ".git\index.lock" del /f /q ".git\index.lock" >nul 2>&1
if exist ".git\rebase-merge" git rebase --abort >nul 2>&1
rd /q ".git\rebase-merge" >nul 2>&1

echo   [..]   Passo 1 de 4: guardando o que estiver solto aqui...
git add -A
git diff --cached --quiet
if errorlevel 1 git commit -q -m "Trabalho local antes de arrumar o workflow"
echo   [ok]   Nada pendente.
echo.

echo   [..]   Passo 2 de 4: trazendo o que esta no GitHub...
git pull --no-rebase --no-edit origin main
if errorlevel 1 goto ERRO_PULL
echo   [ok]   Em dia.
echo.

echo   [..]   Passo 3 de 4: pondo o ponto na frente...
if exist ".github\workflows\coleta-diaria.yml" goto JA_ARRUMADO
if not exist "github\workflows\coleta-diaria.yml" goto NAO_ACHEI
git mv github .github
if errorlevel 1 goto ERRO_MV
git commit -q -m "O workflow precisa morar em .github, com o ponto: sem ele o Actions nao le"
echo   [ok]   Agora e .github\workflows\coleta-diaria.yml
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
echo     Pronto.
echo   =====================================================
echo.
echo   Confira agora: abra a aba Actions do repositorio.
echo     https://github.com/Xigante/adelaide-jobs/actions
echo   Tem que aparecer "Coleta diaria" na lateral esquerda.
echo.
echo   Depois cadastre os segredos em:
echo     https://github.com/Xigante/adelaide-jobs/settings/secrets/actions
echo.
echo   Pode apagar este arquivo.
goto FIM

:JA_ARRUMADO
echo   [ok]   Ja estava com o ponto. Nada a fazer aqui.
echo.
echo   Se a aba Actions continua vazia, me mande um print dela.
goto FIM

:NAO_ACHEI
echo   [ERRO] Nao achei nem "github\workflows\coleta-diaria.yml"
echo          nem ".github\workflows\coleta-diaria.yml".
echo.
echo   Ou o arquivo nao subiu, ou esta com outro nome.
echo   Me mande um print de:
echo     https://github.com/Xigante/adelaide-jobs
goto FIM

:ERRO_PULL
echo.
echo   [ERRO] Nao consegui trazer o que esta no GitHub.
echo          Nada foi perdido. Me mande esta tela.
goto FIM

:ERRO_MV
echo.
echo   [ERRO] O git nao conseguiu renomear a pasta.
echo          Quase sempre e o OneDrive segurando o arquivo:
echo          pause a sincronizacao e rode este .bat de novo.
goto FIM

:ERRO_PUSH
echo.
echo   [ERRO] O envio falhou, mas o renomear funcionou aqui no PC.
echo          Rode o ENVIAR-PARA-GITHUB.bat para terminar,
echo          ou me mande esta tela.
goto FIM

:SEM_GIT
echo   [ERRO] O Git nao esta instalado.
echo   Baixe em https://git-scm.com/download/win

:FIM
echo.
pause
endlocal
