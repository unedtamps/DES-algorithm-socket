import json
import socket
import threading

import lib

messages = []
client_key = ""
server_key = "db4b60092e536e47"
key = server_key
SERVER = "SERVER"


def extract_message(message):
    message = json.loads(message)
    return message["body"], message["sender"]


def create_message(body, sender):
    return json.dumps({"sender": sender, "body": lib.des_encrypt(body, key)})


def recive_message(client_socket):
    global key
    while True:
        msg = client_socket.recv(1024).decode()
        if not msg:
            break

        message, sender = extract_message(msg)

        if sender == SERVER:
            key = server_key
        else:
            key = client_key

        message = lib.des_decrypt(message, key).replace("\x00", "")
        # print(repr(message))
        # print("connected" in message.lower().strip())
        # print("CONNECTED" == message)
        if "CONNECTED" in message or "JOINED" in message or "DISCONNECTED" in message:
            key = client_key

        print(f"({sender}) {message}")


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5054  # socket server port number
    global client_key

    username = input("Input your username: ")
    client_key = input("Input your client key: ")

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    client_thread = threading.Thread(
        target=recive_message,
        args=(client_socket,),
    )
    client_thread.start()

    while True:
        try:
            message = input()  # take input
        except:
            print("Keyboard interupt")
            break

        if message == "":
            print("Cannot send blank")
            continue

        try:
            client_socket.send(
                create_message(message, username).encode()
            )  # send message
        except:
            print("Not valid input")
            break

        print("\033[1A" + "\033[K", end="")
        print(f"(you) {message}")
    client_socket.close()


if __name__ == "__main__":
    client_program()
