# Maven dependency graph: variant 11

Practical work 2, stages 1-2. The application reads settings from CSV,
downloads the POM of the selected Maven package version, and prints its
declared direct dependencies. Stages 3-5 are not implemented yet.

## Requirements

Python 3.10 or later. No third-party packages or compilation are needed.

## Configuration

The chosen CSV layout has two columns with the header `key,value`:

```csv
key,value
package,junit:junit
version,4.13.2
repository,https://repo.maven.apache.org/maven2
test_mode,false
```

The assignment requires the four settings; the column names and layout
are the representation chosen for this program.

| Setting | Meaning |
|---|---|
| `package` | Name of the package to analyze. |
| `version` | Version of the package to analyze. |
| `repository` | Repository URL or path to a test repository file. |
| `test_mode` | `true` for a local file, `false` for a real repository. |

All four settings must be present and nonempty. Mode must be `true` or
`false`. In real mode, the repository URL must have a scheme and
hostname. In test mode, the repository must be an existing file; relative
paths are interpreted against the CSV directory.

In real mode, `package` identifies a Maven artifact as `groupId:artifactId`.
The package version is used in the requested POM URL. Package and version
values have no additional regular-expression restrictions. Missing packages
or versions produce a repository request error.

## Stage 2

For `junit:junit`, version `4.13.2`, the application requests:

```text
https://repo.maven.apache.org/maven2/junit/junit/4.13.2/junit-4.13.2.pom
```

Dots in groupId become slashes. The POM is downloaded with Python's standard
`urllib.request` and parsed with `xml.etree.ElementTree`. No package manager
or third-party dependency library is used. No JAR files are downloaded.

Only the project's own `dependencies` section is read. Entries inside
`dependencyManagement`, build plugins, or profiles are not treated as direct
declarations. All scopes in the direct section are included, including test
dependencies. Each result is printed as `groupId:artifactId`.

This is a simple POM reader, not a complete Maven effective-model resolver:
parent inheritance and property interpolation are not implemented. It does
not fetch the dependencies' POMs or build a transitive graph at this stage.

Example output with the supplied configuration:

```text
Direct dependencies for junit:junit:4.13.2:
org.hamcrest:hamcrest-core
org.hamcrest:hamcrest-library
```

If the section is empty, the program prints `No direct dependencies.`.
Network and POM parsing failures print `Dependency loading error: ...`.
In test mode, the settings are validated and a stage 3 notice is displayed;
local graph analysis will be implemented at that stage.

## Run

From the repository root:

```powershell
python -B DependencyGraph/src/main.py
.\DependencyGraph\run.bat
python -B DependencyGraph/src/main.py --config DependencyGraph/tests/config_test.csv
```

By default the program reads `DependencyGraph/config.csv`. The optional
`--config` argument selects another CSV. All analysis settings come from
that file.

Configuration errors are reported as `Configuration error: ...`. Exit code
0 means success; exit code 1 means a configuration or dependency-load error.

## Functions

| Function | Purpose |
|---|---|
| `read_config(path)` | Read the two-column CSV into a dictionary. |
| `validate_config(config, config_path)` | Check the four settings. |
| `get_dependencies(package, version, repository)` | Download and read direct POM dependencies. |
| `main()` | Read, validate, print, and handle errors. |

## Demonstration and tests

```powershell
.\DependencyGraph\tests\test_stage1.ps1
.\DependencyGraph\tests\test_stage2.ps1
python -B -m unittest discover -s DependencyGraph/tests -p 'test_*.py' -v
```

The stage 2 demonstration downloads the real POM selected in `config.csv`.
The stage 1 script still checks configuration errors, using the current
program version. Automated tests cover configuration errors, URL assembly
for the requested version, direct-section parsing, empty dependencies, XML
errors, and network errors. Automated tests replace HTTP responses with
small XML examples; only the PowerShell demonstration needs network access.
