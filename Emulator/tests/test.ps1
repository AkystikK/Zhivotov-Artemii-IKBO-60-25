param([Parameter(Mandatory = $true)][string]$FixtureDir)

$main = Join-Path $PSScriptRoot "../src/main.py"
$archive = Join-Path $FixtureDir "multiple.zip"
$startup = Join-Path $PSScriptRoot "startup.txt"
python -B $main --vfs $archive --script $startup
if ($LASTEXITCODE -ne 0) { throw "Startup test failed." }
