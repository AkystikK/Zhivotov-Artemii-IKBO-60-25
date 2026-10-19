import getpass
import socket

username = getpass.getuser()
hostname = socket.gethostname() 


while True:
    command = input(f"{username}@{hostname}:~$ ")
    parts = command.split()

    if not parts:
        continue
    
    commandName = parts[0]
    commandArgs = parts[1:]

    match commandName:

        case "exit":
            if commandArgs:
                print("Error: command exit cant accept arguments")
            else:
                break

        case "ls":
            if len(commandArgs) <= 1:
                print(f"Command: {commandName}, arguments: {commandArgs}")
            else:
                print(f"Error: incorrect arguments: {commandArgs}")

        case "cd":
            if len(commandArgs) <= 1:
                print(f"Command: {commandName}, arguments: {commandArgs}")
            else:
                print(f"Error: incorrect arguments: {commandArgs}")

        case _:
            print(f"Error: unknown command: {commandName}")


           
