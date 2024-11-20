import json
import os
import socket
import threading

from dotenv import load_dotenv

import lib
from rsa import RSA
from server import get_public_key, send_public_key

load_dotenv()

messages = []
client_key = ""
server_key = "db4b60092e536e47"
key = server_key
SERVER = "SERVER"
SERVER_PUBLIC_KEY = None
PRIVATE_KEY = None
PUBLIC_KEY = None


def extract_message(message):
    message = json.loads(message)
    return message["body"], message["sender"]


def create_message(body, sender):
    key_dec = lib.key_generation()
    print(key_dec)
    rsa_encrypt_key = RSA().encrypt(SERVER_PUBLIC_KEY, key_dec)
    return json.dumps(
        {
            "sender": sender,
            "body": lib.des_encrypt(body, key_dec),
            "message_key": rsa_encrypt_key,
        }
    )


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
        if "CONNECTED" in message or "JOINED" in message or "DISCONNECTED" in message:
            key = client_key

        print(f"({sender}) {message}")


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = int(os.getenv("SERVER_PORT", "5500"))
    global client_key
    global PRIVATE_KEY, PUBLIC_KEY, SERVER_PUBLIC_KEY

    try:
        username = input("Username: ")
        client_key = input("Message key: ")

        if not username:
            raise ValueError("Username cannot empty")

        if len(client_key) != 16:
            raise ValueError("Key must 64bit")

    except ValueError as e:
        print(f"Error : {e}")
        return

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server

    # send id for public key

    id_temp = lib.key_generation()
    PUBLIC_KEY, PRIVATE_KEY = RSA().generate_keys()
    send_public_key(PUBLIC_KEY, id_temp)
    SERVER_PUBLIC_KEY = get_public_key(SERVER)
    client_socket.send(create_message(id_temp, username).encode())

    client_thread = threading.Thread(
        target=recive_message,
        args=(client_socket,),
    )
    client_thread.start()

    while True:
        try:
            message = input()  # take input
        except:
            print("interupt")
            break

        if message == "":
            print("Cannot send blank")
            continue

        try:
            client_socket.send(create_message(message, username).encode())
        except:
            print("Not valid input")
            break

        print("\033[1A" + "\033[K", end="")
        print(f"(you) {message}")

    client_socket.close()


if __name__ == "__main__":
    client_program()
