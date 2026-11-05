# Runs the ingest CLI; all arguments are passed through.
# Examples:
#   .\tools\ingest.ps1 connect google --context personal   # opens a browser login
#   .\tools\ingest.ps1 accounts                            # lists connected accounts
$ErrorActionPreference = "Stop"
$apps = Join-Path $PSScriptRoot "..\apps"
uv --directory $apps run ap-bubble-ingest @args
exit $LASTEXITCODE
