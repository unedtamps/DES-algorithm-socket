import json
import os
import random
import socket
import threading
from logging import log

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
N1 = random.randint(1, 2000)
N2 = 0


def extract_message(message):
    message = json.loads(message)
    return (
        message["body"],
        message["sender"],
        message["message_key"],
        message["n2"],
    )


def create_message(body, sender):
    global SERVER_PUBLIC_KEY
    key_dec = lib.key_generation()
    rsa_encrypt_key = RSA().encrypt(SERVER_PUBLIC_KEY, key_dec)
    return json.dumps(
        {
            "sender": sender,
            "body": lib.des_encrypt(body, key_dec),
            "message_key": rsa_encrypt_key,
            "n2": RSA().encrypt(SERVER_PUBLIC_KEY, N2),
        }
    )


def recive_message(client_socket):
    while True:
        global PRIVATE_KEY, PUBLIC_KEY, N2
        msg = client_socket.recv(1024).decode()
        if not msg:
            break

        message, sender, message_key, n2 = extract_message(msg)
        des_key = RSA().decrypt(PRIVATE_KEY, message_key)
        n2 = RSA().decrypt(PRIVATE_KEY, n2)
        if n2 != N2:
            print("Connection not secure")
            continue
        message = lib.des_decrypt(message, des_key).replace("\x00", "")
        # if sender == SERVER and ("CONNECTED" in message):
        #     PUBLIC_KEY, PRIVATE_KEY = RSA().generate_keys()
        #     lib.send_public_key(PUBLIC_KEY, username, PA_U)

        print(f"({sender}) {message}")


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = int(os.getenv("SERVER_PORT", "5500"))
    global PRIVATE_KEY, PUBLIC_KEY, SERVER_PUBLIC_KEY, N2

    try:
        username = input("Username: ")

        if not username:
            raise ValueError("Username cannot empty")

    except ValueError as e:
        print(f"Error : {e}")
        return

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    SERVER_PUBLIC_KEY = lib.get_public_key(SERVER, PA_U)
    username = f"{username}-{random.randint(1,30000)}"
    PUBLIC_KEY, PRIVATE_KEY = RSA().generate_keys()
    lib.send_public_key(PUBLIC_KEY, username, PA_U)

    n1 = str(random.randint(1, 1000))
    n1_encrypted = RSA().encrypt(SERVER_PUBLIC_KEY, n1)
    message_key = lib.key_generation()
    encrypted_key = RSA().encrypt(SERVER_PUBLIC_KEY, message_key)
    msg = json.dumps(
        {
            "sender": username,
            "body": lib.des_encrypt("Connected", message_key),
            "message_key": encrypted_key,
            "n1": n1_encrypted,
        }
    )
    print("Starting handshake..")
    client_socket.send(msg.encode())
    message = json.loads(client_socket.recv(1024).decode())
    get_des_key = RSA().decrypt(PRIVATE_KEY, message["message_key"])
    msg = (lib.des_decrypt(message["body"], get_des_key),)
    n1_server = RSA().decrypt(PRIVATE_KEY, message["n1"])
    N2 = RSA().decrypt(PRIVATE_KEY, message["n2"])

    if n1_server != n1:
        print("Server connection not the same")
        return
    print("Hanshake accepted")
    msg = create_message("Connection accepted", username)
    client_socket.send(msg.encode())

    # send id for public key and handshake

    # client_socket.send(
    #     create_message(f"Connection from: {username}", username).encode()
    # )

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
