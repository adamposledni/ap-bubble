# Runs the web app for development: API on http://127.0.0.1:8787, UI on http://localhost:5173.
# Ctrl+C stops both.
$ErrorActionPreference = "Stop"
$apps = (Resolve-Path (Join-Path $PSScriptRoot "..\apps")).Path
$web = Join-Path $apps "ap-bubble-web"
$env:COREPACK_ENABLE_DOWNLOAD_PROMPT = "0"

$api = Start-Process uv -ArgumentList "--directory", $apps, "run", "ap-bubble-api" -NoNewWindow -PassThru
Push-Location $web
try {
    corepack pnpm install --frozen-lockfile
    corepack pnpm dev
}
finally {
    Pop-Location
    taskkill /PID $api.Id /T /F | Out-Null
}
