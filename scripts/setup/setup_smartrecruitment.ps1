param(
    [string]$ProjectRoot = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$Folders = @(
    "backend",
    "frontend",
    "testing\scripts\unit",
    "testing\scripts\integration",
    "testing\scripts\regression",
    "testing\scripts\deployment",
    "testing\results\unit",
    "testing\results\integration",
    "testing\results\regression",
    "testing\results\deployment",
    "testing\fixtures",
    "scripts\setup",
    "scripts\deployment",
    "scripts\backup",
    "scripts\validation",
    "config",
    "data\GeoReference",
    "backups",
    "logs",
    "docs"
)

Write-Host "=== SMARTRECRUITMENT FOLDER SETUP ==="
Write-Host "ROOT: $ProjectRoot"
Write-Host "DRY RUN: $DryRun"

foreach ($Folder in $Folders) {
    $Target = Join-Path $ProjectRoot $Folder

    if (Test-Path -LiteralPath $Target -PathType Leaf) {
        throw "PATH CONFLICT: A file occupies folder path $Target"
    }

    if (Test-Path -LiteralPath $Target -PathType Container) {
        Write-Host "EXISTS: $Folder"
    }
    elseif ($DryRun) {
        Write-Host "WOULD CREATE: $Folder"
    }
    else {
        New-Item -ItemType Directory -Path $Target -Force | Out-Null
        Write-Host "CREATED: $Folder"
    }
}

Write-Host "SETUP COMPLETED"
Write-Host "Existing files overwritten: NO"
Write-Host "Existing application folders moved: NO"
