$ErrorActionPreference = "Stop"
$WorkTemp = Join-Path $PWD ".tmp\install-temp"
New-Item -ItemType Directory -Force -Path $WorkTemp | Out-Null
$env:TEMP = $WorkTemp
$env:TMP = $WorkTemp
$NpmCache = Join-Path $WorkTemp "npm-cache"
New-Item -ItemType Directory -Force -Path $NpmCache | Out-Null
Write-Host "[1/3] Installing frontend dependencies..."
& npm.cmd install --cache "$NpmCache"
if ($LASTEXITCODE -ne 0) {
  if (Test-Path node_modules) {
    Write-Warning "npm install failed, but node_modules already exists. Continuing with existing frontend dependencies."
  } else {
    throw "npm install failed with exit code $LASTEXITCODE"
  }
}
Write-Host "[2/3] Creating backend virtualenv..."
Set-Location backend
$PythonLauncher = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
  py -3.11 --version *> $null
  if ($LASTEXITCODE -eq 0) {
    $PythonLauncher = @("py", "-3.11")
  } else {
    py -3.12 --version *> $null
    if ($LASTEXITCODE -eq 0) {
      $PythonLauncher = @("py", "-3.12")
    }
  }
}
if (-not $PythonLauncher) {
  throw "Python 3.11 or 3.12 is required. Install Python 3.11, open a new PowerShell, then rerun this script. Python 3.14 may try to build pydantic-core from source and fail without Visual Studio C++ Build Tools."
}
if (Test-Path .venv) {
  $venvHome = ""
  $venvVersion = ""
  if (Test-Path .\.venv\pyvenv.cfg) {
    $homeLine = Get-Content .\.venv\pyvenv.cfg | Where-Object { $_ -like "home = *" } | Select-Object -First 1
    if ($homeLine) {
      $venvHome = $homeLine.Substring("home = ".Length).Trim()
    }
    $versionLine = Get-Content .\.venv\pyvenv.cfg | Where-Object { $_ -like "version = *" } | Select-Object -First 1
    if ($versionLine) {
      $venvVersion = $versionLine.Substring("version = ".Length).Trim()
    }
  }
  if ($venvHome -and !(Test-Path (Join-Path $venvHome "python.exe"))) {
    Write-Host "Existing .venv is invalid. Recreating it..."
    Remove-Item .venv -Recurse -Force
  } elseif ($venvVersion -and !($venvVersion.StartsWith("3.11") -or $venvVersion.StartsWith("3.12"))) {
    Write-Host "Existing .venv uses Python $venvVersion. Recreating it with Python 3.11/3.12..."
    Remove-Item .venv -Recurse -Force
  } elseif (!(Test-Path .\.venv\Scripts\pip.exe)) {
    Write-Host "Existing .venv has no pip. Recreating it..."
    Remove-Item .venv -Recurse -Force
  }
}
if (!(Test-Path .venv)) {
  & $PythonLauncher[0] $PythonLauncher[1] -m venv .venv
  if ($LASTEXITCODE -ne 0) {
    throw "Python virtualenv creation failed with exit code $LASTEXITCODE"
  }
}
.\.venv\Scripts\python.exe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
  throw "pip upgrade failed with exit code $LASTEXITCODE"
}
.\.venv\Scripts\pip.exe install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
  throw "backend dependency install failed with exit code $LASTEXITCODE"
}
if (!(Test-Path .env)) { Copy-Item .env.example .env }
Set-Location ..
Write-Host "[3/3] Done. Edit backend\.env, then run scripts\start-dev.ps1"
