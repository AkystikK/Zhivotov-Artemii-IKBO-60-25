import getpass
import socket
import argparse
import zipfile
import base64

from pathlib import PurePosixPath

def runCommand(command):
    parts = command.split()

    if not parts:
        return 0

    commandName = parts[0]
    commandArgs = parts[1:]

    match commandName:

        case "exit":
            if commandArgs:
                print("Error: command exit cant accept arguments")
                return 1
            else:
                return 2

        case "ls":
            if len(commandArgs) <= 1:
                print(f"Command: {commandName}, arguments: {commandArgs}")
            else:
                print(f"Error: incorrect arguments: {commandArgs}")
                return 1

        case "cd":
            if len(commandArgs) <= 1:
                print(f"Command: {commandName}, arguments: {commandArgs}")
            else:
                print(f"Error: incorrect arguments: {commandArgs}")
                return 1

        case _:
            print(f"Error: unknown command: {commandName}")
            return 1

    return 0


def addDirectory(vfs, path):
    if path in vfs and vfs[path]["type"] != "directory":
        raise ValueError(f"A file conflicts with directory {path}")

    vfs[path] = {"type": "directory"}


def loadVfs(source):
    vfs = {"/": {"type": "directory"}}

    with zipfile.ZipFile(source, "r") as archive:
        for entry in archive.infolist():
            path = PurePosixPath(entry.filename)

            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ValueError(f"Invalid VFS path: {entry.filename}")

            for parent in reversed(path.parents):
                if parent != PurePosixPath("."):
                    addDirectory(vfs, "/" + parent.as_posix())

            name = "/" + path.as_posix()

            if entry.is_dir():
                addDirectory(vfs, name)
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


def printVfs(vfs):
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
        vfs = loadVfs(args.vfs)

    except (OSError, zipfile.BadZipFile, ValueError) as error:
        print(f"VFS loading error: {error}")
        raise SystemExit(1)

    printVfs(vfs)

    if args.script:
        try:
            with open(args.script, encoding="utf-8") as startScript:
                for command in startScript:
                    command = command.rstrip("\n")
                    print(f"{username}@{hostname}:~$ {command}")

                    res = runCommand(command)

                    if(res == 1):
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

        res = runCommand(command)

        if(res == 2):
            break
