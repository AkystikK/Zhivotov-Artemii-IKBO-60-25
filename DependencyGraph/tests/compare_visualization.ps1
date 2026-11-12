param(
    [Parameter(Mandatory = $true)][string]$WorkDir,
    [string]$Maven = "mvn",
    [string]$Repository
)

$WorkDir = [System.IO.Path]::GetFullPath($WorkDir)

if (-not $Repository) {
    $Repository = Join-Path $WorkDir "repository"
}

$project = Split-Path $PSScriptRoot -Parent

foreach ($name in @("junit", "hamcrest_library", "hamcrest_core")) {
    $folder = Join-Path $WorkDir $name
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
    $settings = @{}

    foreach ($row in (Import-Csv "$project/examples/$name.csv")) {
        $settings[$row.key] = $row.value
    }

    $parts = $settings["package"].Split(":")
    [xml]$pom = Get-Content -LiteralPath "$PSScriptRoot/maven/pom.xml"
    $pom.project.dependencies.dependency.groupId = $parts[0]
    $pom.project.dependencies.dependency.artifactId = $parts[1]
    $pom.project.dependencies.dependency.version = $settings["version"]
    $pom.Save("$folder/pom.xml")

    & $Maven --batch-mode --no-transfer-progress -f "$folder/pom.xml" `
        "-Dmaven.repo.local=$Repository" `
        "org.apache.maven.plugins:maven-dependency-plugin:3.8.1:tree" `
        "-DoutputType=dot" "-DoutputFile=$folder/maven.dot" `
        *> "$folder/maven.log"

    if ($LASTEXITCODE -ne 0) {
        throw "Maven visualization failed: $name. See $folder/maven.log"
    }

    Write-Host "Maven DOT: $folder/maven.dot"
}
