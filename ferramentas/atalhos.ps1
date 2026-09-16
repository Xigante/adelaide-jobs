# Cria os atalhos na area de trabalho.
#
# Arquivo separado de proposito. O CRIAR-ATALHO.bat antigo carregava
# este mesmo codigo como -EncodedCommand: um bloco de base64 de 2 KB,
# ilegivel, que ninguem conseguia corrigir sem reencodar tudo. Como
# -File, da para ler e mexer.
$ErrorActionPreference = 'Stop'

$aqui = $env:AQUI.TrimEnd('\')
$desk = [Environment]::GetFolderPath('Desktop')
if (-not $desk) { Write-Output 'SEM-DESKTOP'; exit 3 }

$sh = New-Object -ComObject WScript.Shell
$feitos = @()

function Novo-Atalho($nome, $alvo, $desc, $icone, $pastaDeTrabalho) {
  if (-not (Test-Path $alvo)) { return $false }
  $lnk = Join-Path $desk ($nome + '.lnk')
  $a = $sh.CreateShortcut($lnk)
  $a.TargetPath       = $alvo
  $a.WorkingDirectory = $pastaDeTrabalho
  $a.Description      = $desc
  $a.WindowStyle      = 1
  if ($icone -and (Test-Path $icone.Split(',')[0])) { $a.IconLocation = $icone }
  $a.Save()
  return (Test-Path $lnk)
}

# 1. O de todo dia.
$alvo  = Join-Path $aqui 'ATUALIZAR-VAGAS.bat'
$icone = Join-Path $aqui 'play.ico'
if (-not (Test-Path $alvo)) { Write-Output 'SEM-ALVO'; exit 2 }
if (Novo-Atalho ([char]0x25B6 + ' Atualizar vagas') $alvo `
      'Busca vagas novas em Adelaide. Cerca de 10 minutos. Rode uma vez por dia.' `
      "$icone,0" $aqui) { $feitos += 'atualizar' }

# 2. A caixa de ferramentas. Sem isto, achar os outros sete botoes
#    depende de lembrar o caminho da pasta dentro do OneDrive — e nao
#    lembrar disso ja travou uma mudanca de PC.
if (Novo-Atalho 'Ferramentas - adelaide-jobs' $aqui `
      'Os botoes do adelaide-jobs: enviar para o GitHub, configurar e-mail, reparar banco, levar para outro PC.' `
      'shell32.dll,4' $aqui) { $feitos += 'ferramentas' }

if ($feitos.Count -eq 0) { Write-Output 'FALHOU'; exit 4 }
Write-Output 'CRIADO'
Write-Output $desk
Write-Output ($feitos -join ',')
