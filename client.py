import json
import socket
import threading
from os import pardir

import lib

messages = []


def extract_message(message):
    message = json.loads(message)
    return message["body"], message["sender"]


def create_message(body, sender):
    return json.dumps({"sender": sender, "body": body})


def recive_message(client_socket, key):
    while True:
        msg = client_socket.recv(1024).decode()
        if not msg:
            break

        print(msg)
        message, sender = extract_message(msg)
        print(f"({sender}) {lib.des_decrypt(message, key)}")


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5056  # socket server port number

    username = input("Input your username: ")
    encrypt_key = input("Input encrypt the key: ")

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    client_thread = threading.Thread(
        target=recive_message,
        args=(
            client_socket,
            encrypt_key,
        ),
    )
    client_thread.start()

    while True:
        message = input()  # take input
        try:
            client_socket.send(
                create_message(lib.des_encrypt(message, encrypt_key), username).encode()
            )  # send message
        except:
            print("Connection Closed")
            break

        if message.lower().strip() == "bye":
            break

        print("\033[1A" + "\033[K", end="")
        print(f"(you) {message}")

    client_socket.close()  # close the connection


if __name__ == "__main__":
    client_program()
