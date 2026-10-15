param(
    [string]$SourceRoot = "C:\SmartRecruitment\GitWorkspace\SmartRecruitment2026",
    [string]$TargetRoot = "C:\GitWorkspace\SmartRecruitment2026",
    [string]$ActiveFrontend = "C:\SmartRecruitment\CloudResourcingUI-Final",
    [string]$GeoSource = "C:\SmartRecruitment\GeoReference\geonames_cities.sqlite"
)

$ErrorActionPreference = "Stop"

Write-Host "=== SMARTRECRUITMENT WINDOWS MIGRATION PLAN ==="

$Items = @(
    @{
        Name = "Git history"
        Source = Join-Path $SourceRoot ".git"
        Target = Join-Path $TargetRoot ".git"
    },
    @{
        Name = "Python backend"
        Source = Join-Path $SourceRoot "Pybackend-Final-2026"
        Target = Join-Path $TargetRoot "backend"
    },
    @{
        Name = "React frontend"
        Source = $ActiveFrontend
        Target = Join-Path $TargetRoot "frontend"
    },
    @{
        Name = "GeoNames database"
        Source = $GeoSource
        Target = Join-Path $TargetRoot "data\GeoReference\geonames_cities.sqlite"
    }
)

$Errors = 0

foreach ($Item in $Items) {
    Write-Host ""
    Write-Host "COMPONENT: $($Item.Name)"
    Write-Host "SOURCE: $($Item.Source)"
    Write-Host "TARGET: $($Item.Target)"

    if (!(Test-Path -LiteralPath $Item.Source)) {
        Write-Host "ERROR: Source missing"
        $Errors++
        continue
    }

    if ($Item.Name -eq "Git history" -or $Item.Name -eq "GeoNames database") {
        if (Test-Path -LiteralPath $Item.Target) {
            Write-Host "ERROR: Destination already occupied"
            $Errors++
            continue
        }
    } else {
        $Existing = @(Get-ChildItem -LiteralPath $Item.Target -Force -ErrorAction Stop)
        if ($Existing.Count -gt 0) {
            Write-Host "ERROR: Destination is not empty"
            $Errors++
            continue
        }
    }

    Write-Host "READY FOR MIGRATION"
}

Write-Host ""
Write-Host "SOURCE FILES MODIFIED: NO"
Write-Host "DESTINATION FILES MODIFIED: NO"
Write-Host "PRODUCTION MODIFIED: NO"

if ($Errors -gt 0) {
    throw "MIGRATION READINESS FAILED: $Errors issue(s)"
}

Write-Host "MIGRATION DRY RUN: PASS"
