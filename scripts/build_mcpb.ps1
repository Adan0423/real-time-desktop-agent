param(
    [string]$Version = "3.0.1-beta"
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$dist = Join-Path $root "dist"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$stage = Join-Path $dist "mcpb-staging-$stamp"
$output = Join-Path $dist "real-time-desktop-agent-$Version.mcpb"

New-Item -ItemType Directory -Force $stage | Out-Null

Copy-Item -LiteralPath (Join-Path $root "packaging\mcpb\manifest.json") -Destination (Join-Path $stage "manifest.json")
Copy-Item -LiteralPath (Join-Path $root "pyproject.toml") -Destination $stage
Copy-Item -LiteralPath (Join-Path $root "mcpb_server.py") -Destination $stage
Copy-Item -LiteralPath (Join-Path $root "README.md") -Destination $stage
Copy-Item -LiteralPath (Join-Path $root "LICENSE") -Destination $stage
Copy-Item -LiteralPath (Join-Path $root "packaging\mcpb\icon.png") -Destination $stage
Copy-Item -LiteralPath (Join-Path $root "src") -Destination $stage -Recurse

npx @anthropic-ai/mcpb validate (Join-Path $stage "manifest.json")
npx @anthropic-ai/mcpb pack $stage $output

Write-Output $output
