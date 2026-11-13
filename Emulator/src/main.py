"""Run a shell emulator with a ZIP filesystem stored in memory."""

import argparse
import base64
import getpass
import socket
import zipfile
from pathlib import PurePosixPath


def run_command(command):
    """Run one command and return its internal status code."""
    parts = command.split()

    if not parts:
        return 0

    command_name = parts[0]
    command_args = parts[1:]

    match command_name:

        case "exit":
            if command_args:
                print("Error: command exit cant accept arguments")
                return 1
            else:
                return 2

        case "ls":
            if len(command_args) <= 1:
                print(f"Command: {command_name}, arguments: {command_args}")
            else:
                print(f"Error: incorrect arguments: {command_args}")
                return 1

        case "cd":
            if len(command_args) <= 1:
                print(f"Command: {command_name}, arguments: {command_args}")
            else:
                print(f"Error: incorrect arguments: {command_args}")
                return 1

        case _:
            print(f"Error: unknown command: {command_name}")
            return 1

    return 0


def add_directory(vfs, path):
    """Add a directory and reject a conflicting file."""
    if path in vfs and vfs[path]["type"] != "directory":
        raise ValueError(f"A file conflicts with directory {path}")

    vfs[path] = {"type": "directory"}


def load_vfs(source):
    """Read a ZIP archive into an in-memory filesystem."""
    vfs = {"/": {"type": "directory"}}

    with zipfile.ZipFile(source, "r") as archive:
        for entry in archive.infolist():
            path = PurePosixPath(entry.filename)

            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ValueError(f"Invalid VFS path: {entry.filename}")

            for parent in reversed(path.parents):
                if parent != PurePosixPath("."):
                    add_directory(vfs, "/" + parent.as_posix())

            name = "/" + path.as_posix()

            if entry.is_dir():
                add_directory(vfs, name)
            else:
                if name in vfs:
                    raise ValueError(f"Duplicate VFS path: {name}")

                data = archive.read(entry)

                vfs[name] = {
                    "type": "file",
                    "content": base64.b64encode(data).decode("ascii"),
                    "size": len(data),
                }

    return vfs


def print_vfs(vfs):
    """Print loaded paths, types, sizes, and entry counts."""
    files = 0
    directories = 0

    for path, node in sorted(vfs.items()):
        if node["type"] == "directory":
            print(f"DEBUG: VFS directory {path}")
            directories += 1
        else:
            print(f"DEBUG: VFS file {path}, size={node['size']} bytes")
            files += 1

    print(f"DEBUG: VFS loaded: {directories} directories, {files} files")


if __name__ == "__main__":
    username = getpass.getuser()
    hostname = socket.gethostname()

    parser = argparse.ArgumentParser()
    parser.add_argument("--vfs", required=True)
    parser.add_argument("--script")

    args = parser.parse_args()

    print(f"DEBUG: vfs_path = {args.vfs}")
    print(f"DEBUG: script_path = {args.script}")

    try:
        vfs = load_vfs(args.vfs)

    except (OSError, zipfile.BadZipFile, ValueError) as error:
        print(f"VFS loading error: {error}")
        raise SystemExit(1)

    print_vfs(vfs)

    if args.script:
        try:
            with open(args.script, encoding="utf-8") as start_script:
                for command in start_script:
                    command = command.rstrip("\n")
                    print(f"{username}@{hostname}:~$ {command}")

                    res = run_command(command)

                    if res == 1:
                        print("Startup script stopped.")
                        break
                    elif res == 2:
                        raise SystemExit(0)

        except OSError as error:
            print(f"Script reading error: '{args.script}': {error}")

    while True:
        try:
            command = input(f"{username}@{hostname}:~$ ")

        except (EOFError, KeyboardInterrupt):
            print()
            break

        res = run_command(command)

        if res == 2:
            break
