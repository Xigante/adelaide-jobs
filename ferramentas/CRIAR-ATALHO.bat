@echo off
setlocal
title adelaide-jobs - criar o botao na area de trabalho

echo.
echo   =====================================================
echo     Criar o botao "Atualizar vagas" na area de trabalho
echo   =====================================================
echo.
echo   Rode este arquivo UMA VEZ. Depois pode esquecer que ele existe.
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
if not exist "%~dp0ATUALIZAR-VAGAS.bat" (
  echo   [ERRO] Nao achei ATUALIZAR-VAGAS.bat ao lado deste arquivo.
  echo   Este arquivo tem que ficar dentro da pasta australia.
  goto FIM
)

echo   [..]   Criando o atalho...

set "SAIDA="
set "ONDE="
for /f "delims=" %%L in ('powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand JABFAHIAcgBvAHIAQQBjAHQAaQBvAG4AUAByAGUAZgBlAHIAZQBuAGMAZQAgAD0AIAAnAFMAdABvAHAAJwAKACQAYQBxAHUAaQAgACAAPQAgACQAZQBuAHYAOgBBAFEAVQBJAC4AVAByAGkAbQBFAG4AZAAoACcAXAAnACkACgAkAGEAbAB2AG8AIAAgAD0AIABKAG8AaQBuAC0AUABhAHQAaAAgACQAYQBxAHUAaQAgACcAQQBUAFUAQQBMAEkAWgBBAFIALQBWAEEARwBBAFMALgBiAGEAdAAnAAoAJABpAGMAbwBuAGUAIAA9ACAASgBvAGkAbgAtAFAAYQB0AGgAIAAkAGEAcQB1AGkAIAAnAHAAbABhAHkALgBpAGMAbwAnAAoAaQBmACAAKAAtAG4AbwB0ACAAKABUAGUAcwB0AC0AUABhAHQAaAAgACQAYQBsAHYAbwApACkAIAB7ACAAVwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAiAFMARQBNAC0AQQBMAFYATwAiADsAIABlAHgAaQB0ACAAMgAgAH0ACgAkAGQAZQBzAGsAIAA9ACAAWwBFAG4AdgBpAHIAbwBuAG0AZQBuAHQAXQA6ADoARwBlAHQARgBvAGwAZABlAHIAUABhAHQAaAAoACcARABlAHMAawB0AG8AcAAnACkACgBpAGYAIAAoAC0AbgBvAHQAIAAkAGQAZQBzAGsAKQAgAHsAIABXAHIAaQB0AGUALQBPAHUAdABwAHUAdAAgACIAUwBFAE0ALQBEAEUAUwBLAFQATwBQACIAOwAgAGUAeABpAHQAIAAzACAAfQAKACQAbABuAGsAIAA9ACAASgBvAGkAbgAtAFAAYQB0AGgAIAAkAGQAZQBzAGsAIAAoAFsAYwBoAGEAcgBdADAAeAAyADUAQgA2ACAAKwAgACcAIABBAHQAdQBhAGwAaQB6AGEAcgAgAHYAYQBnAGEAcwAuAGwAbgBrACcAKQAKACQAcwBoACAAPQAgAE4AZQB3AC0ATwBiAGoAZQBjAHQAIAAtAEMAbwBtAE8AYgBqAGUAYwB0ACAAVwBTAGMAcgBpAHAAdAAuAFMAaABlAGwAbAAKACQAYQAgAD0AIAAkAHMAaAAuAEMAcgBlAGEAdABlAFMAaABvAHIAdABjAHUAdAAoACQAbABuAGsAKQAKACQAYQAuAFQAYQByAGcAZQB0AFAAYQB0AGgAIAAgACAAIAAgACAAIAAgAD0AIAAkAGEAbAB2AG8ACgAkAGEALgBXAG8AcgBrAGkAbgBnAEQAaQByAGUAYwB0AG8AcgB5ACAAIAA9ACAAJABhAHEAdQBpAAoAJABhAC4ARABlAHMAYwByAGkAcAB0AGkAbwBuACAAIAAgACAAIAAgACAAPQAgACcAQgB1AHMAYwBhACAAdgBhAGcAYQBzACAAbgBvAHYAYQBzACAAZQBtACAAQQBkAGUAbABhAGkAZABlAC4AIABDAGUAcgBjAGEAIABkAGUAIAAxADAAIABtAGkAbgB1AHQAbwBzAC4AIABSAG8AZABlACAAdQBtAGEAIAB2AGUAegAgAHAAbwByACAAZABpAGEALgAnAAoAJABhAC4AVwBpAG4AZABvAHcAUwB0AHkAbABlACAAIAAgACAAIAAgACAAPQAgADEACgBpAGYAIAAoAFQAZQBzAHQALQBQAGEAdABoACAAJABpAGMAbwBuAGUAKQAgAHsAIAAkAGEALgBJAGMAbwBuAEwAbwBjAGEAdABpAG8AbgAgAD0AIAAiACQAaQBjAG8AbgBlACwAMAAiACAAfQAKACQAYQAuAFMAYQB2AGUAKAApAAoAaQBmACAAKABUAGUAcwB0AC0AUABhAHQAaAAgACQAbABuAGsAKQAgAHsAIABXAHIAaQB0AGUALQBPAHUAdABwAHUAdAAgACIAQwBSAEkAQQBEAE8AIgA7ACAAVwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAkAGQAZQBzAGsAIAB9ACAAZQBsAHMAZQAgAHsAIABXAHIAaQB0AGUALQBPAHUAdABwAHUAdAAgACIARgBBAEwASABPAFUAIgA7ACAAZQB4AGkAdAAgADQAIAB9AA== 2^>nul') do (
  if not defined SAIDA (set "SAIDA=%%L") else (if not defined ONDE set "ONDE=%%L")
)

if /i "%SAIDA%"=="CRIADO" goto OK
if /i "%SAIDA%"=="SEM-ALVO" goto ERRO_ALVO
if /i "%SAIDA%"=="SEM-DESKTOP" goto ERRO_DESKTOP
goto ERRO_GERAL

:OK
echo   [ok]   Pronto.
echo.
echo          Procure na sua area de trabalho um circulo verde
echo          com um triangulo branco, chamado:
echo.
echo              ^> Atualizar vagas
echo.
echo          (fica em %ONDE%)
echo.
echo   A partir de agora, dois cliques nele e so esperar.
echo   Nao precisa mais achar esta pasta.
goto FIM

:ERRO_ALVO
echo   [ERRO] O PowerShell nao achou o ATUALIZAR-VAGAS.bat.
goto MANUAL

:ERRO_DESKTOP
echo   [ERRO] Nao consegui descobrir onde fica a sua area de trabalho.
goto MANUAL

:ERRO_GERAL
echo   [ERRO] O Windows bloqueou a criacao automatica do atalho.
echo          Isso acontece em maquina de empresa com politica restrita.
goto MANUAL

:MANUAL
echo.
echo   Da para fazer na mao em 5 segundos:
echo.
echo     1. clique com o botao DIREITO em ATUALIZAR-VAGAS.bat
echo     2. Mostrar mais opcoes  (so no Windows 11)
echo     3. Enviar para  ^>  Area de trabalho (criar atalho)
echo.
echo   Depois clique com o direito no atalho que apareceu,
echo   Renomear, e chame do que voce quiser.
goto FIM

:FIM
echo.
pause
endlocal
