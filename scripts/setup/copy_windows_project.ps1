$ErrorActionPreference = "Stop"

$OldGit = "C:\SmartRecruitment\GitWorkspace\SmartRecruitment2026"
$OldFrontend = "C:\SmartRecruitment\CloudResourcingUI-Final"
$NewRoot = "C:\GitWorkspace\SmartRecruitment2026"

function Copy-SafeDirectory {
    param(
        [string]$Source,
        [string]$Target,
        [string[]]$ExcludeDirs = @(),
        [string[]]$ExcludeFiles = @()
    )

    if (!(Test-Path -LiteralPath $Source -PathType Container)) {
        throw "Source directory missing: $Source"
    }

    if (!(Test-Path -LiteralPath $Target -PathType Container)) {
        throw "Destination directory missing: $Target"
    }

    if (@(Get-ChildItem -LiteralPath $Target -Force).Count -gt 0) {
        throw "Destination not empty: $Target"
    }

    $Args = @($Source, $Target, "/E", "/R:1", "/W:1", "/NP")

    if ($ExcludeDirs.Count -gt 0) {
        $Args += "/XD"
        $Args += $ExcludeDirs
    }

    if ($ExcludeFiles.Count -gt 0) {
        $Args += "/XF"
        $Args += $ExcludeFiles
    }

    & robocopy @Args | Out-Null
    $Code = $LASTEXITCODE

    if ($Code -ge 8) {
        throw "Robocopy failed with exit code $Code : $Source"
    }

    $CopiedFiles = @(Get-ChildItem -LiteralPath $Target -Recurse -File -Force)

    foreach ($File in $CopiedFiles) {
        $Relative = $File.FullName.Substring($Target.Length).TrimStart('\')
        $Original = Join-Path $Source $Relative

        if (!(Test-Path -LiteralPath $Original -PathType Leaf)) {
            throw "Original file missing during verification: $Original"
        }

        $OriginalHash = (Get-FileHash -LiteralPath $Original -Algorithm SHA256).Hash
        $CopiedHash = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash

        if ($OriginalHash -ne $CopiedHash) {
            throw "SHA256 MISMATCH: $Relative"
        }
    }

    Write-Host "COPY VERIFIED: $Source ($($CopiedFiles.Count) files)"
}

Write-Host "=== STEP 6P.26G.9 - WINDOWS PROJECT MIGRATION ==="

$GitTarget = Join-Path $NewRoot ".git"

if (Test-Path -LiteralPath $GitTarget) {
    throw "Git destination already exists. Refusing overwrite."
}

Write-Host "=== COPYING GIT HISTORY ==="
New-Item -ItemType Directory -Path $GitTarget | Out-Null

Copy-SafeDirectory `
    -Source "$OldGit\.git" `
    -Target $GitTarget

Write-Host "=== COPYING PYTHON BACKEND ==="

Copy-SafeDirectory `
    -Source "$OldGit\Pybackend-Final-2026" `
    -Target "$NewRoot\backend" `
    -ExcludeDirs @("venv", ".venv", "__pycache__") `
    -ExcludeFiles @("*.pyc", "*.bak")

Write-Host "=== COPYING ACTIVE REACT FRONTEND ==="

Copy-SafeDirectory `
    -Source $OldFrontend `
    -Target "$NewRoot\frontend" `
    -ExcludeDirs @("node_modules", "build") `
    -ExcludeFiles @("*.bak", ".env.before_*")

Write-Host "=== COPYING GEONAMES DATABASE ==="

$GeoSource = "C:\SmartRecruitment\GeoReference\geonames_cities.sqlite"
$GeoTarget = "$NewRoot\data\GeoReference\geonames_cities.sqlite"

if (Test-Path -LiteralPath $GeoTarget) {
    throw "GeoNames destination already exists."
}

Copy-Item -LiteralPath $GeoSource -Destination $GeoTarget -ErrorAction Stop

Write-Host "=== CHECKING GEONAMES SHA256 ==="

$SourceHash = (Get-FileHash -LiteralPath $GeoSource -Algorithm SHA256).Hash
$TargetHash = (Get-FileHash -LiteralPath $GeoTarget -Algorithm SHA256).Hash

if ($SourceHash -ne $TargetHash) {
    throw "GeoNames checksum mismatch."
}

Write-Host "GEONAMES SHA256: MATCH"
Write-Host "SOURCE DIRECTORIES MODIFIED: NO"
Write-Host "AZURE PRODUCTION MODIFIED: NO"
Write-Host "COPY MIGRATION COMPLETED"
