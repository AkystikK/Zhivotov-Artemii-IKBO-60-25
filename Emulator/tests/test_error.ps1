param([Parameter(Mandatory = $true)][string]$FixtureDir)

$main = Join-Path $PSScriptRoot "../src/main.py"
$archive = Join-Path $FixtureDir "multiple.zip"
$cases = @("startup_error.txt", "startup_bad_ls.txt",
    "startup_bad_cd.txt", "startup_bad_exit.txt")
foreach ($name in $cases) {
    Write-Host "Testing startup error: $name"
    $startup = Join-Path $PSScriptRoot $name
    "exit" | python -B $main --vfs $archive --script $startup
    if ($LASTEXITCODE -ne 0) { throw "Startup error test failed." }
}
