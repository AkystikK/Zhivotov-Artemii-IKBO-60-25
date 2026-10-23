param([Parameter(Mandatory = $true)][string]$FixtureDir)

$main = Join-Path $PSScriptRoot "../src/main.py"
$startup = Join-Path $PSScriptRoot "startup_vfs.txt"
foreach ($name in @("minimal.zip", "multiple.zip", "deep.zip")) {
    Write-Host "Testing VFS: $name"
    $archive = Join-Path $FixtureDir $name
    python -B $main --vfs $archive --script $startup
    if ($LASTEXITCODE -ne 0) { throw "VFS test failed: $name" }
}
