import os
import socket

from dotenv import load_dotenv

import lib
from rsa import RSA

## nanti  bakal ada database di pka ini untuk semuanya jadi nanti server balkal
## minta public key untuk semua yang ada bebas public key

PR_A = (571969, 2295287)


key_database = []

load_dotenv()


def socket_charge():
    global key_database
    host = socket.gethostname()
    pka_port = int(os.getenv("PKA_PORT", "5000"))
    server_socket = socket.socket()
    server_socket.bind((host, pka_port))
    server_socket.listen()

    while True:
        print("Waiting for connections ...")
        conn, address = server_socket.accept()  # accept new connection
        print("Connection from: " + str(address))
        msg = conn.recv(1024).decode()
        if msg == "1":
            msg = conn.recv(1024).decode()
            msg = lib.string_to_list(msg)
            msg = RSA().decrypt(PR_A, msg)
            key = msg.split(",")
            key_database.append(
                {"id": key[0], "public_key": (key[1], key[2]), "timeout": 1200}
            )

            print("List Users:")
            for i in key_database:
                print(f'id: {i["id"]}')
                print(f'public_key: {i["public_key"]}')
                print(f'timeout: {i["timeout"]}')

        elif msg == "2":
            msg = conn.recv(1024).decode()
            msg = lib.string_to_list(msg)
            msg = RSA().decrypt(PR_A, msg)
            for i in key_database:
                if i["id"] == msg:
                    e, n = i["public_key"]
                    m = f"{e},{n}"
                    m = RSA().encrypt(PR_A, m)
                    conn.send(lib.list_to_string(m).encode())
                    break
            else:
                conn.send("0,0".encode())
        elif msg == "3":
            msg = conn.recv(1024).decode()
            key_database = [i for i in key_database if i["id"] != msg]


if __name__ == "__main__":
    socket_charge()
