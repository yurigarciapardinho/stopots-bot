$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RuntimePath = Join-Path (Split-Path -Parent $ProjectRoot) ".runtime"
$EnvironmentPath = Join-Path $RuntimePath "venv-desktop-windows"
Set-Location $ProjectRoot
py -3.12 -m venv $EnvironmentPath
if ($LASTEXITCODE -ne 0) { throw "Instale Python 3.12 com o lançador py antes de continuar." }
$PythonPath = Join-Path $EnvironmentPath "Scripts\python.exe"
& $PythonPath -m pip install --disable-pip-version-check ".[desktop]"
if ($LASTEXITCODE -ne 0) { throw "Não foi possível instalar o aplicativo." }
$ShortcutPath = Join-Path $ProjectRoot "StopotS Assistente.lnk"
$ShellObject = New-Object -ComObject WScript.Shell
$Shortcut = $ShellObject.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = Join-Path $EnvironmentPath "Scripts\pythonw.exe"
$Shortcut.Arguments = '-m stopots_v2.desktop'
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Save()
Write-Host "Atalho criado em $ShortcutPath. Instale Google Chrome para jogar."
