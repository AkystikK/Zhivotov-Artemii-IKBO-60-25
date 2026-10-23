param([Parameter(Mandatory = $true)][string]$FixtureDir)

$main = Join-Path $PSScriptRoot "../src/main.py"
$archive = Join-Path $FixtureDir "multiple.zip"
python -B $main
if ($LASTEXITCODE -ne 2) { throw "Expected a missing parameter error." }
python -B $main --vfs
if ($LASTEXITCODE -ne 2) { throw "Expected a missing value error." }
python -B $main --vfs $archive --script
if ($LASTEXITCODE -ne 2) { throw "Expected a missing script value error." }
$missing = Join-Path $PSScriptRoot "missing.txt"
"exit" | python -B $main --vfs $archive --script $missing
if ($LASTEXITCODE -ne 0) { throw "Missing script test failed." }
