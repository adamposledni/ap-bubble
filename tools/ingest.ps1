# Runs the ingest CLI; all arguments are passed through.
# Examples:
#   .\tools\ingest.ps1 connect google --context personal   # opens a browser login
#   .\tools\ingest.ps1 accounts                            # lists connected accounts
#   .\tools\ingest.ps1 sync google_calendar                # ingests a source's changes into L0
#                         (sources: google_calendar, google_tasks)
$ErrorActionPreference = "Stop"
$apps = Join-Path $PSScriptRoot "..\apps"
uv --directory $apps run ap-bubble-ingest @args
exit $LASTEXITCODE
