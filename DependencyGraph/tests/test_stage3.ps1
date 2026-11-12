$project = Split-Path $PSScriptRoot -Parent
$main = Join-Path $project "src/main.py"

foreach ($name in @("single", "chain", "shared", "cycle")) {
    Write-Host "Testing graph: $name"
    $config = Join-Path $PSScriptRoot "config_$name.csv"
    python -B $main --config $config

    if ($LASTEXITCODE -ne 0) {
        throw "Graph test failed: $name"
    }
}
