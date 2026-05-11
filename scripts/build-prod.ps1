$ErrorActionPreference = "Stop"
Write-Host "[1/3] Building React PWA..."
npm install
npm run build
Write-Host "[2/3] Checking Python compile..."
Set-Location backend
python -m compileall app
Set-Location ..
Write-Host "[3/3] Production build and backend compile completed."
