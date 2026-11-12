$project = Split-Path $PSScriptRoot -Parent
$main = Join-Path $project "src/main.py"

foreach ($name in @("junit", "hamcrest_library", "hamcrest_core")) {
    Write-Host "Testing PlantUML: $name"
    $config = Join-Path $project "examples/$name.csv"
    python -B $main --config $config --plantuml

    if ($LASTEXITCODE -ne 0) {
        throw "PlantUML generation failed: $name"
    }
}
