#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Verify the fallback scanner catches all expected patterns in test fixtures.
.DESCRIPTION
    Runs scan-fallbacks.py against each test fixture file and checks
    that every known pattern is detected. Exits 0 if all pass, 1 on failure.
#>

$ScriptDir = Split-Path -Parent $PSCommandPath
$ProjectDir = Split-Path -Parent $ScriptDir
$FixtureDir = Join-Path $ScriptDir "test-cases"
$Scanner = Join-Path $ScriptDir "scan-fallbacks.py"
$TempDir = Join-Path $ScriptDir ".verify-tmp"

$TotalTests = 0
$Passed = 0
$Failed = 0

$ExpectedFindings = @(
    # go-sample.go
    @{ File = "go-sample.go"; Code = "F005"; Line = 12 }
    @{ File = "go-sample.go"; Code = "F005"; Line = 13 }
    @{ File = "go-sample.go"; Code = "F005"; Line = 20 }

    # java-sample.java
    @{ File = "java-sample.java"; Code = "F001"; Line = 5 }
    @{ File = "java-sample.java"; Code = "F001"; Line = 14 }
    @{ File = "java-sample.java"; Code = "F002"; Line = 23 }
    @{ File = "java-sample.java"; Code = "F003"; Line = 29 }
    @{ File = "java-sample.java"; Code = "F003"; Line = 34 }
    @{ File = "java-sample.java"; Code = "F005"; Line = 41 }
    @{ File = "java-sample.java"; Code = "F008"; Line = 48 }

    # kotlin-sample.kt
    @{ File = "kotlin-sample.kt"; Code = "F003"; Line = 4 }
    @{ File = "kotlin-sample.kt"; Code = "F003"; Line = 8 }
    @{ File = "kotlin-sample.kt"; Code = "F003"; Line = 12 }
    @{ File = "kotlin-sample.kt"; Code = "F001"; Line = 21 }
    @{ File = "kotlin-sample.kt"; Code = "F002"; Line = 32 }
    @{ File = "kotlin-sample.kt"; Code = "F012"; Line = 40 }

    # csharp-sample.cs
    @{ File = "csharp-sample.cs"; Code = "F001"; Line = 6 }
    @{ File = "csharp-sample.cs"; Code = "F005"; Line = 16 }
    @{ File = "csharp-sample.cs"; Code = "F002"; Line = 24 }
    @{ File = "csharp-sample.cs"; Code = "F004"; Line = 30 }

    # typescript-sample.ts
    @{ File = "typescript-sample.ts"; Code = "F003"; Line = 3 }
    @{ File = "typescript-sample.ts"; Code = "F003"; Line = 12 }
    @{ File = "typescript-sample.ts"; Code = "F004"; Line = 12 }
    @{ File = "typescript-sample.ts"; Code = "F001"; Line = 20 }
    @{ File = "typescript-sample.ts"; Code = "F002"; Line = 29 }

    # python-sample.py
    @{ File = "python-sample.py"; Code = "F010"; Line = 6 }
    @{ File = "python-sample.py"; Code = "F001"; Line = 14 }
    @{ File = "python-sample.py"; Code = "F002"; Line = 22 }
    @{ File = "python-sample.py"; Code = "F005"; Line = 30 }
    @{ File = "python-sample.py"; Code = "F005"; Line = 39 }
    @{ File = "python-sample.py"; Code = "F004"; Line = 44 }
    @{ File = "python-sample.py"; Code = "F007"; Line = 53 }

    # rust-sample.rs
    @{ File = "rust-sample.rs"; Code = "F009"; Line = 3 }
    @{ File = "rust-sample.rs"; Code = "F009"; Line = 8 }
    @{ File = "rust-sample.rs"; Code = "F009"; Line = 13 }
    @{ File = "rust-sample.rs"; Code = "F003"; Line = 13 }
    @{ File = "rust-sample.rs"; Code = "F012"; Line = 16 }
    @{ File = "rust-sample.rs"; Code = "F012"; Line = 19 }
)

function Write-Result {
    param([string]$Label, [bool]$Passed)
    if ($Passed) {
        Write-Host "  PASS: $Label" -ForegroundColor Green
    } else {
        Write-Host "  FAIL: $Label" -ForegroundColor Red
    }
}

# Clean and create temp dir
if (Test-Path $TempDir) { Remove-Item -Recurse -Force $TempDir }
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

try {
    # Copy fixture files into a flat temp directory
    Get-ChildItem -Path $FixtureDir -Filter "*.go" | Copy-Item -Destination $TempDir
    Get-ChildItem -Path $FixtureDir -Filter "*.java" | Copy-Item -Destination $TempDir
    Get-ChildItem -Path $FixtureDir -Filter "*.kt" | Copy-Item -Destination $TempDir
    Get-ChildItem -Path $FixtureDir -Filter "*.cs" | Copy-Item -Destination $TempDir
    Get-ChildItem -Path $FixtureDir -Filter "*.ts" | Copy-Item -Destination $TempDir
    Get-ChildItem -Path $FixtureDir -Filter "*.py" | Copy-Item -Destination $TempDir
    Get-ChildItem -Path $FixtureDir -Filter "*.rs" | Copy-Item -Destination $TempDir

    # Run scanner for each language
    $AllFindings = @()
    $Languages = @("go", "java", "kotlin", "csharp", "typescript", "python", "rust")
    foreach ($lang in $Languages) {
        $jsonPath = Join-Path $TempDir "findings-$lang.json"
        python $Scanner --dir $TempDir --lang $lang --json $jsonPath 2>$null
        if (Test-Path $jsonPath) {
            $report = Get-Content $jsonPath | ConvertFrom-Json
            foreach ($f in $report.findings) {
                $f.file = Split-Path -Leaf $f.file
                $AllFindings += $f
            }
        }
    }

    Write-Host "`n=== Verification Results ===" -ForegroundColor Cyan
    $TotalTests = $ExpectedFindings.Count

    foreach ($expected in $ExpectedFindings) {
        $label = "$($expected.File):$($expected.Line) [$($expected.Code)]"
        $found = $AllFindings | Where-Object {
            $_.file -eq $expected.File -and
            $_.line -eq $expected.Line -and
            $_.code -eq $expected.Code
        }
        if ($found) {
            Write-Result -Label $label -Passed $true
            $Passed++
        } else {
            Write-Result -Label $label -Passed $false
            $Failed++
        }
    }

    # Check for false positives in legitimate code
    $KnownGoodLines = @(51, 52, 53, 54, 55)  # java-sample.java: orElseGet is legitimate
    $Unexpected = $AllFindings | Where-Object {
        $_.file -eq "java-sample.java" -and $_.line -in $KnownGoodLines
    }
    if ($Unexpected) {
        foreach ($f in $Unexpected) {
            Write-Host "  WARN: False positive on legitimate code at $($f.file):$($f.line) [$($f.code)]" -ForegroundColor Yellow
            $Failed++
        }
    }

    Write-Host "`n=== Summary ===" -ForegroundColor Cyan
    Write-Host "Total: $TotalTests, Passed: $Passed, Failed: $Failed"

    if ($Failed -gt 0) {
        exit 1
    }
    exit 0
}
finally {
    Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
}
