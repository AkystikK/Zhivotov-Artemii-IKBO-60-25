$project = Split-Path $PSScriptRoot -Parent
$main = Join-Path $project "src/main.py"
$config = Join-Path $project "config.csv"

python -B $main --config $config

if ($LASTEXITCODE -ne 0) {
    throw "Direct dependency loading failed."
}
