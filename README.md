# Configuration Management coursework

Variant 11. The Python shell emulator in `Emulator` implements stages 1-3.
The earlier Bash practical is preserved in `prac1.md`.

## Requirements and scope

- Python 3.10 or later; only the standard library is used.
- Windows PowerShell for the demonstration scripts.
- No compilation, package installation, or virtual environment is required.
- The prompt uses the actual operating-system username and hostname.
- Input is split on whitespace; shell quoting and flags are not implemented.
- `ls` and `cd` are stubs accepting zero or one argument.
- `exit` accepts no arguments and terminates the emulator.
- Stage 4 command implementations and stage 5 commands are outside this project.

## Stage 3: in-memory VFS

`--vfs` identifies a ZIP archive on the real filesystem. The loader opens it
read-only and reads its entries into a Python dictionary. It never extracts
entries to disk, writes to the archive, or keeps file contents in host folders.
Reading and decompressing an entry into memory is distinct from extracting it
to the host filesystem.

Dictionary keys are absolute UNIX-style virtual paths. The root `/` always
exists. Parent directories omitted from ZIP metadata are created in memory.
Explicit empty directories and empty files are preserved.

```python
{
    "/": {"type": "directory"},
    "/docs": {"type": "directory"},
    "/docs/note.txt": {
        "type": "file",
        "content": "SGVsbG8=",
        "size": 5,
    },
}
```

All file contents, including text, are stored as Base64 ASCII strings. Base64
is reversible encoding, not encryption; `base64.b64decode(content)` restores
the original bytes. `size` records the original byte count.

On startup, debug output lists the loaded paths, types, and file sizes. This
demonstrates loading the VFS while `ls` and `cd` remain stage 1 stubs. The stubs
do not check virtual path existence or change the current directory.

Missing, invalid, and damaged ZIP files produce a readable error and process
exit code 1. Duplicate files, conflicting file/directory paths, and absolute
or parent-traversing archive entry paths are rejected. Successful loading
leaves the archive unchanged.

## Program functions

| Function | Purpose |
|---|---|
| `loadVfs(source)` | Read a ZIP path or file-like object into the VFS dictionary. |
| `addDirectory(vfs, path)` | Add a directory and reject file/directory conflicts. |
| `printVfs(vfs)` | Display the loaded structure for stage 3 verification. |
| `runCommand(command)` | Split and dispatch one command. |

All emulator code is in `Emulator/src/main.py`. Below the functions, the
`if __name__ == "__main__":` block parses settings, loads the VFS, executes
the startup script, and starts the interactive loop. Importing this file
from the tests does not start the emulator.

Command results are internal status codes: 0 means success, 1 means a command
error, and 2 means an exit request. These are separate from process exit codes.
A startup command or file-open error stops script execution and enters
interactive mode. An `exit` in the script terminates the entire emulator.
Startup files are UTF-8 text containing one emulator command per line.

## Generate test archives

Run the following commands in PowerShell from the repository root. Generated
archives belong outside the repository and are not committed.

```powershell
$scratch = Join-Path $env:USERPROFILE 'Documents\CodexScratch\tasks'
$task = Join-Path $scratch '2026-10-23-emulator-stage3'
$fixtures = Join-Path $task 'fixtures'
python -B Emulator/tests/create_vfs_fixtures.py --output-dir $fixtures
```

The generator creates:

| File | Contents |
|---|---|
| `minimal.zip` | An empty ZIP; the VFS contains only `/`. |
| `multiple.zip` | Several files, all 256 byte values, and an empty directory. |
| `deep.zip` | Files under `documents/course/week1` and an empty subdirectory. |
| `invalid.zip` | Non-ZIP data for a format error. |
| `corrupt.zip` | A ZIP entry with damaged contents for a CRC error. |

`createFixtures` builds the dataset, `writeArchive` writes fixture ZIPs, and
`createCorruptArchive` deliberately damages one fixture. Only this test-data
generator writes archives; the emulator itself reads them without modification.

## Run the emulator

```powershell
$archive = Join-Path $fixtures 'deep.zip'
python -B Emulator/src/main.py --vfs $archive
python -B Emulator/src/main.py --vfs $archive --script Emulator/tests/startup_vfs.txt
.\run.bat --vfs $archive --script Emulator/tests/startup_vfs.txt
python -B Emulator/src/main.py --help
```

`--vfs` is required; `--script` is optional. Both values are printed at startup.
Relative paths are resolved against the caller's current working directory.
Quote paths containing spaces when writing them literally in a command.

Example excerpt:

```text
DEBUG: VFS file /documents/course/week1/data.bin, size=4 bytes
username@hostname:~$ ls /
Command: ls, arguments: ['/']
username@hostname:~$ cd /documents/course/week1
Command: cd, arguments: ['/documents/course/week1']
```

## Run tests

Generate fixtures first, then run the automated tests:

```powershell
$env:VFS_FIXTURE_DIR = $fixtures
python -B -m unittest discover -s Emulator/tests -p 'test_*.py' -v
```

The tests cover in-memory loading, byte-for-byte Base64 recovery, implicit
directories, empty entries, three directory levels, invalid ZIPs, damaged
contents, unchanged source hashes, absence of extracted files, command errors,
startup stopping, parameter validation, and interactive behavior.

PowerShell demonstrations accept the generated fixture directory explicitly.
Their program and startup paths use `$PSScriptRoot`, so the scripts can also
be launched from a different working directory.

```powershell
.\Emulator\tests\test.ps1 -FixtureDir $fixtures
.\Emulator\tests\test_vfs.ps1 -FixtureDir $fixtures
.\Emulator\tests\test_vfs_errors.ps1 -FixtureDir $fixtures
.\Emulator\tests\test_error.ps1 -FixtureDir $fixtures
.\Emulator\tests\test_launch_errors.ps1 -FixtureDir $fixtures
.\Emulator\tests\test_interactive.ps1 -FixtureDir $fixtures
```

The first two scripts demonstrate successful startup and all three valid VFS
variants. The next three demonstrate VFS errors, command errors, and invalid
launch parameters. Error diagnostics in those runs are expected. The final
script opens interactive mode; enter `ls`, `cd /`, and `exit` manually.
Separate startup files are used for separate errors because a single startup
script must stop at its first error.
