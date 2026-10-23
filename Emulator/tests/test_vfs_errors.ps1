param([Parameter(Mandatory = $true)][string]$FixtureDir)

$main = Join-Path $PSScriptRoot "../src/main.py"
$startup = Join-Path $PSScriptRoot "startup_vfs.txt"
foreach ($name in @("missing.zip", "invalid.zip", "corrupt.zip")) {
    Write-Host "Testing VFS load error: $name"
    $archive = Join-Path $FixtureDir $name
    python -B $main --vfs $archive --script $startup
    if ($LASTEXITCODE -ne 1) { throw "Expected a VFS load error: $name" }
}
