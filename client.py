import json
import socket
import threading

messages = []


def extract_message(message):
    message = json.loads(message)
    return message["body"], message["sender"]


def create_message(body, sender):
    return json.dumps({"sender": sender, "body": body})


def recive_message(client_socket):
    while True:
        message, sender = extract_message(client_socket.recv(1024).decode())
        print(f"({sender}) {message}")


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5052  # socket server port number

    username = input("Input your username: ")

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    threading.Thread(target=recive_message, args=(client_socket,)).start()

    while True:
        # message, sender = extract_message(client_socket.recv(1024).decode())
        # print(f"({sender}) {message}")

        message = input()  # take input
        print("\033[1A" + "\033[K", end="")
        print(f"(you) {message}")
        client_socket.send(create_message(message, username).encode())  # send message

        if message.lower().strip == "bye":
            break

    client_socket.close()  # close the connection


if __name__ == "__main__":
    client_program()
