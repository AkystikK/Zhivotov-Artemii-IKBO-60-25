# Maven dependency graph: variant 11

Practical work 2, stage 1. The application reads four settings from CSV,
checks them, and prints each setting as `key = value`.
Stages 2-5 are not implemented yet.

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

Package and version values have no additional character restrictions.
Checking whether the selected package/version exists belongs to the data
collection stage. There are no network requests at stage 1.

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

Errors are reported as `Configuration error: ...`. Exit code 0 means
success; exit code 1 means a configuration error.

## Functions

| Function | Purpose |
|---|---|
| `read_config(path)` | Read the two-column CSV into a dictionary. |
| `validate_config(config, config_path)` | Check the four settings. |
| `main()` | Read, validate, print, and handle errors. |

## Demonstration and tests

```powershell
.\DependencyGraph\tests\test_stage1.ps1
python -B -m unittest discover -s DependencyGraph/tests -p 'test_*.py' -v
```

The demonstration shows valid configurations and errors for every setting.
The tests also check missing settings and a missing configuration file.
