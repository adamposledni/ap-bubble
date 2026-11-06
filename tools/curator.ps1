# Runs the curator CLI; all arguments are passed through.
# Examples:
#   .\tools\curator.ps1 run --dry-run      # only writes the batch files (see the run's folder
#                                          # under %LOCALAPPDATA%\ap-bubble\curator\runs)
#   .\tools\curator.ps1 run                # curates with Claude Code (uses your Claude seat)
$ErrorActionPreference = "Stop"
$apps = Join-Path $PSScriptRoot "..\apps"
uv --directory $apps run ap-bubble-curator @args
exit $LASTEXITCODE
