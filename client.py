import json
import os
import socket
import threading

from dotenv import load_dotenv

import lib
from rsa import RSA

load_dotenv()

messages = []
SERVER = "SERVER"
SERVER_PUBLIC_KEY = None
PRIVATE_KEY = None
PUBLIC_KEY = None
PA_U = (1663177, 2295287)


def extract_message(message):
    message = json.loads(message)
    return message["body"], message["sender"], message["message_key"]


def create_message(body, sender):
    key_dec = lib.key_generation()
    rsa_encrypt_key = RSA().encrypt(SERVER_PUBLIC_KEY, key_dec)
    return json.dumps(
        {
            "sender": sender,
            "body": lib.des_encrypt(body, key_dec),
            "message_key": rsa_encrypt_key,
        }
    )


def recive_message(client_socket, username):
    while True:
        global PRIVATE_KEY, PUBLIC_KEY
        msg = client_socket.recv(1024).decode()
        if not msg:
            break

        message, sender, message_key = extract_message(msg)
        des_key = RSA().decrypt(PRIVATE_KEY, message_key)
        print(f"des key {des_key}")
        message = lib.des_decrypt(message, des_key).replace("\x00", "")
        if sender == SERVER and ("CONNECTED" in message):
            PUBLIC_KEY, PRIVATE_KEY = RSA().generate_keys()
            lib.send_public_key(PUBLIC_KEY, username, PA_U)

        print(f"({sender}) {message}")


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = int(os.getenv("SERVER_PORT", "5500"))
    global PRIVATE_KEY, PUBLIC_KEY, SERVER_PUBLIC_KEY

    try:
        username = input("Username: ")

        if not username:
            raise ValueError("Username cannot empty")

    except ValueError as e:
        print(f"Error : {e}")
        return

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server

    # send id for public key

    id_temp = lib.key_generation()
    PUBLIC_KEY, PRIVATE_KEY = RSA().generate_keys()
    lib.send_public_key(PUBLIC_KEY, id_temp, PA_U)
    SERVER_PUBLIC_KEY = lib.get_public_key(SERVER, PA_U)
    client_socket.send(create_message(id_temp, username).encode())

    client_thread = threading.Thread(
        target=recive_message,
        args=(
            client_socket,
            username,
        ),
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
