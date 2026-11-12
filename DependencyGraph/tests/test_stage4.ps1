$project = Split-Path $PSScriptRoot -Parent
$main = Join-Path $project "src/main.py"

foreach ($name in @("single", "chain", "shared")) {
    Write-Host "Testing loading order: $name"
    $config = Join-Path $PSScriptRoot "config_$name.csv"
    python -B $main --config $config --order

    if ($LASTEXITCODE -ne 0) {
        throw "Loading order failed: $name"
    }
}

Write-Host "Expected cycle error:"
$config = Join-Path $PSScriptRoot "config_cycle.csv"
python -B $main --config $config --order

if ($LASTEXITCODE -ne 1) {
    throw "A cycle must prevent a loading order."
}
