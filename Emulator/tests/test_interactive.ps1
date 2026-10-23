param([Parameter(Mandatory = $true)][string]$FixtureDir)

$main = Join-Path $PSScriptRoot "../src/main.py"
$archive = Join-Path $FixtureDir "minimal.zip"
python -B $main --vfs $archive
if ($LASTEXITCODE -ne 0) { throw "Interactive test failed." }
