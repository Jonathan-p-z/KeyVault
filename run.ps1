Param(
  [string]$Theme = "auto"
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Get-PythonLauncher {
  if (Get-Command py -ErrorAction SilentlyContinue) { return @("py", "-3") }
  if (Get-Command python -ErrorAction SilentlyContinue) { return @("python") }
  return $null
}

$launcher = Get-PythonLauncher
if (-not $launcher) {
  Write-Host "ERREUR: Python n'est pas installe ou n'est pas dans le PATH." -ForegroundColor Red
  Write-Host "Installe Python 3.10+ puis relance ce script." -ForegroundColor Yellow
  Write-Host "https://www.python.org/downloads/" -ForegroundColor Yellow
  Read-Host "Appuie sur Entree pour fermer"
  exit 1
}

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  Write-Host "[1/3] Creation de l'environnement virtuel (.venv)..." -ForegroundColor Cyan
  & $launcher -m venv .venv
}

$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Write-Host "[2/3] Installation / mise a jour des dependances..." -ForegroundColor Cyan
& $py -m pip install -U pip | Out-Null
& $py -m pip install -r requirements.txt

Write-Host "[3/3] Lancement..." -ForegroundColor Cyan
& $py -m mdp_app --theme $Theme
