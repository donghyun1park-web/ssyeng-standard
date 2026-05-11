param([string]$BaseUrl = "http://localhost:8000")
$ErrorActionPreference = "Stop"
$paths = @("/api/health", "/api/diagnostics/status", "/api/diagnostics/checks", "/api/external/status", "/api/mcp/status", "/api/rag/status")
foreach ($path in $paths) {
  $url = "$BaseUrl$path"
  Write-Host "Checking $url"
  Invoke-RestMethod -Uri $url -Method GET | ConvertTo-Json -Depth 8
}
