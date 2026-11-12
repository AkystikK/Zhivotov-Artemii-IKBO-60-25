param(
    [Parameter(Mandatory = $true)][string]$WorkDir,
    [string]$Maven = "mvn"
)

$WorkDir = [System.IO.Path]::GetFullPath($WorkDir)
New-Item -ItemType Directory -Path "$WorkDir/project" -Force | Out-Null
Copy-Item -LiteralPath "$PSScriptRoot/maven/pom.xml" `
    -Destination "$WorkDir/project/pom.xml"

$main = Join-Path $PSScriptRoot "../src/main.py"
$config = Join-Path $PSScriptRoot "config_compare.csv"

python -B $main --config $config --order
if ($LASTEXITCODE -ne 0) { throw "Python loading order failed." }

& $Maven --batch-mode -f "$WorkDir/project/pom.xml" `
    "-Dmaven.repo.local=$WorkDir/repository" `
    "org.apache.maven.plugins:maven-dependency-plugin:3.8.1:resolve" `
    "-DoutputFile=$WorkDir/maven-resolved.txt" `
    *> "$WorkDir/maven.log"

if ($LASTEXITCODE -ne 0) {
    throw "Maven failed. See $WorkDir/maven.log"
}

Get-Content -LiteralPath "$WorkDir/maven-resolved.txt"
