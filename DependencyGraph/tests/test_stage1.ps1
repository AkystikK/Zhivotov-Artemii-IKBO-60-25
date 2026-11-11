$project = Split-Path $PSScriptRoot -Parent
$main = Join-Path $project "src/main.py"

python -B $main
if ($LASTEXITCODE -ne 0) { throw "Default configuration failed." }

$config = Join-Path $PSScriptRoot "config_test.csv"
python -B $main --config $config
if ($LASTEXITCODE -ne 0) { throw "Test configuration failed." }

$cases = @("package", "version", "repository", "mode")

foreach ($name in $cases) {
    Write-Host "Expected configuration error: $name"
    $config = Join-Path $PSScriptRoot "config_bad_$name.csv"
    python -B $main --config $config

    if ($LASTEXITCODE -ne 1) {
        throw "An invalid configuration was accepted: $name"
    }
}
