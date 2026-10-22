import getpass
import socket
import argparse

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

username = getpass.getuser()
hostname = socket.gethostname()

parser = argparse.ArgumentParser()
parser.add_argument("--vfs", required=True)
parser.add_argument("--script")

args = parser.parse_args()

print(f"DEBUG: vfs_path = {args.vfs}")

if args.script:
    print(f"DEBUG: script_path = {args.script}")
    try:
        with open(args.script) as startScript:
            for command in startScript:
                command = command.rstrip("\n")
                print(f"{username}@{hostname}:~$ {command}")

                res = runCommand(command)

                if(res == 1):
                    break
                elif res == 2:
                    raise SystemExit(0)

    except OSError as error:
        print(f"Script reading error: '{args.script}': {error}")

while True:
    command = input(f"{username}@{hostname}:~$ ")

    res = runCommand(command)

    if(res == 2):
        break
