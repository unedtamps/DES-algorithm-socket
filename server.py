import json
import os
import random
import socket
import threading
import time

from dotenv import load_dotenv
from sympy.ntheory.generate import randint

import lib
from client import PUBLIC_KEY
from rsa import RSA

load_dotenv()

database = []
# username
SERVER = "SERVER"
PA_U = (1663177, 2295287)
PRIVATE_KEY = None
# jadi server ini yang bakal minta public key dari pka, dan memasukkannya ke
# dalam databae untuk semua public key, dan kalau sudah semua baru lah  bisa di
# jalankan


# def delete_public_key(key, username):
#     pka_host = socket.gethostname()
#     pka_port = int(os.getenv("PKA_PORT", "5000"))
#     pka_server_socket = socket.socket()
#     pka_server_socket.connect((pka_host, pka_port))
#     pka_server_socket.send("3".encode())
#     time.sleep(0.1)
#     e, n = key
#     msg = f"{username},{e},{n}"
#     pka_server_socket.send(msg.encode())


def extract_message(message, user_public_key):
    if not message:
        return "", "", "", ""
    message = json.loads(message)
    message["n2"] = RSA().decrypt(PRIVATE_KEY, message["n2"])
    message["n2"] = RSA().decrypt(user_public_key, lib.string_to_list(message["n2"]))
    return message["body"], message["sender"], message["message_key"], message["n2"]


def create_message(body, sender, user_public_key, message_key, n2, sender_public_key):
    ##  decrypt message that user send with server publick key
    decrypt_msg_key = RSA().decrypt(PRIVATE_KEY, message_key)
    decrypt_msg_key = RSA().decrypt(
        sender_public_key, lib.string_to_list(decrypt_msg_key)
    )
    ## send key with user to send public key
    encrypted_key = RSA().encrypt(PRIVATE_KEY, decrypt_msg_key)
    encrypted_key = RSA().encrypt(user_public_key, lib.list_to_string(encrypted_key))

    n2 = RSA().encrypt(PRIVATE_KEY, n2)
    n2 = RSA().encrypt(user_public_key, lib.list_to_string(n2))

    return json.dumps(
        {
            "sender": sender,
            "body": body,
            "message_key": encrypted_key,
            "n2": n2,
        }
    )


def server_create_message(body, sender, user_public_key, n2):
    message_key = lib.key_generation()
    encrypted_key = RSA().encrypt(PRIVATE_KEY, message_key)
    encrypted_key = RSA().encrypt(user_public_key, lib.list_to_string(encrypted_key))
    n2 = RSA().encrypt(PRIVATE_KEY, n2)
    n2 = RSA().encrypt(user_public_key, lib.list_to_string(n2))

    return json.dumps(
        {
            "sender": sender,
            "body": lib.des_encrypt(body, message_key),
            "message_key": encrypted_key,
            "n2": n2,
        }
    )


def server_extract_message(message, user_public_key):
    if not message:
        return "", "", ""
    message = json.loads(message)
    get_des_key = RSA().decrypt(PRIVATE_KEY, message["message_key"])
    get_des_key = RSA().decrypt(user_public_key, lib.string_to_list(get_des_key))
    message["n2"] = RSA().decrypt(PRIVATE_KEY, message["n2"])
    message["n2"] = RSA().decrypt(user_public_key, lib.string_to_list(message["n2"]))
    return (
        lib.des_decrypt(message["body"], get_des_key),
        message["sender"],
        message["n2"],
    )


def get_all_connection(key, username):
    for i in database:
        if i["key"] == key:
            # Separate users
            all_except = [user for user in i["user"] if user["username"] != username]
            exact_match = next(
                (user for user in i["user"] if user["username"] == username), None
            )
            return all_except, exact_match
    # Return empty lists if no match found
    return [], None


def single_clinet(conn, username, key):

    while True:
        n2 = 0
        user_public_key = ""
        conns, user_obj = get_all_connection(key, username)
        if user_obj is not None:
            if user_obj["public_key"] is None:
                user_obj["public_key"] = lib.get_public_key(username, PA_U)
                time.sleep(0.2)
            n2 = user_obj["n2"]
            user_public_key = user_obj["public_key"]

        message, sender, message_key, n2_user = extract_message(
            conn.recv(2048).decode(), user_public_key
        )

        if not message:
            break

        print(f"Message from {sender} : {message}")

        print(f" N_user: {n2_user}; N_database : {n2}")
        if n2_user != n2:
            print("n2 not same and valid (message not from the connected user)")
            continue

        if username == sender:
            for j in conns:
                print(f"Sended to : {j['username']}")
                if j["public_key"] is None:
                    j["public_key"] = lib.get_public_key(j["username"], PA_U)
                    time.sleep(0.3)
                msg = create_message(
                    message,
                    sender,
                    j["public_key"],
                    message_key,
                    j["n2"],
                    user_public_key,
                )
                j["conn"].send(msg.encode())
        else:
            print("masuk kirim ke user")
            _, sender_obj = get_all_connection(key, sender)
            sender_key = ""
            if sender_obj is not None:
                if sender_obj["public_key"] is None:
                    sender_obj["public_key"] = lib.get_public_key(username, PA_U)
                    time.sleep(0.2)
                sender_key = sender_obj["public_key"]
            msg = create_message(
                message,
                sender,
                user_public_key,
                message_key,
                n2,
                sender_key,
            )
            conn.send(msg.encode())

    print(f"Connection Close: {username}")
    for chan in database:
        if chan["key"] == key:
            chan["user"] = [
                user for user in chan["user"] if user["username"] != username
            ]

    # conns, user_obj = get_all_connection(key, username)
    # for j in conns:
    #     print(f"Sended to : {j['username']}")
    #     if j["public_key"] is None:
    #         j["public_key"] = lib.get_public_key(j["username"], PA_U)
    #         time.sleep(0.1)
    #     data = server_create_message(
    #         f"{username} DISCONNECTED", SERVER, j["public_key"]
    #     )
    #     j["conn"].send(data.encode())
    conn.close()


def server_program():
    global PRIVATE_KEY
    host = socket.gethostname()
    port = int(os.getenv("SERVER_PORT", "5500"))
    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen()

    # generate key and store to authority
    public_key, PRIVATE_KEY = RSA().generate_keys()
    lib.send_public_key(public_key, SERVER, PA_U)

    while True:
        print("Waiting for connections ...")
        conn, address = server_socket.accept()  # accept new connection
        print("Connection from: " + str(address))
        username = ""
        key = ""
        is_user_exist = False

        # melakukan handshake
        message = json.loads(conn.recv(2048).decode())
        get_des_key = RSA().decrypt(PRIVATE_KEY, message["message_key"])
        msg = lib.des_decrypt(message["body"], get_des_key).replace("\x00", "")
        print(msg)
        username = message["sender"]
        print("Starting handshake...")
        n1 = RSA().decrypt(PRIVATE_KEY, (message["n1"]))

        public_key_user = lib.get_public_key(username, PA_U)
        n1 = RSA().encrypt(public_key_user, n1)
        n2 = str(randint(1, 2000))
        n2_encrypt = RSA().encrypt(public_key_user, str(n2))

        # send message with n1,n2
        message_key = lib.key_generation()
        encrypted_key = RSA().encrypt(public_key_user, message_key)
        msg = json.dumps(
            {
                "sender": SERVER,
                "body": lib.des_encrypt("Connected", message_key),
                "message_key": encrypted_key,
                "n1": n1,
                "n2": n2_encrypt,
            }
        )
        conn.send(msg.encode())

        ## menerima nilai n2 yang di kirm oleh user
        msg, _, n2_user = server_extract_message(
            conn.recv(2048).decode(), public_key_user
        )
        if n2_user != n2:
            print("n2 not same and valid (message not from the connected user)")
            continue

        print("Hanshake accepted")

        # Send menu to the client
        msg = server_create_message(
            "\n1. Make New Channel\n2. Join Channel\n", SERVER, public_key_user, n2
        )
        conn.send(msg.encode())

        menu, username, n2_user = server_extract_message(
            conn.recv(2048).decode(), public_key_user
        )

        if n2_user != n2:
            print("n2 not same and valid (message not from the connected user)")
            continue

        if not menu:
            print(f"Connection Close: {address}")
            conn.close()
            continue
        menu = menu.replace("\x00", "")

        if username.lower().strip() == SERVER.lower().strip():
            data = server_create_message(
                "Username not avaliable: ", SERVER, public_key_user, n2
            )
            conn.send(data.encode())
            print(f"Connection Close: {address}")
            time.sleep(0.1)
            conn.close()
            continue

        if menu == "1":
            key = lib.key_generation()
            data = server_create_message(
                "Enter New Password: ", SERVER, public_key_user, n2
            )
            conn.send(data.encode())
            password, _, n2_user = server_extract_message(
                conn.recv(2048).decode(), public_key_user
            )
            if n2_user != n2:
                print("n2 not same and valid")
                continue

            if not password:
                print(f"Connection Close: {address}")
                conn.close()
                continue

            database.append(
                {
                    "key": key,
                    "password": hash(password),
                    "user": [
                        {
                            "username": username,
                            "conn": conn,
                            "public_key": None,
                            "n2": n2,
                        }
                    ],
                }
            )
            data = server_create_message(
                f"Channel Key : {key}", SERVER, public_key_user, n2
            )
            conn.send(data.encode())
            time.sleep(0.1)
            data = server_create_message(
                "Your are CONNECTED", SERVER, public_key_user, n2
            )
            conn.send(data.encode())
            time.sleep(0.1)
        elif menu == "2":
            # Join Channeli
            is_close = False
            while True:
                data = server_create_message(
                    "Enter Key Channel: ", SERVER, public_key_user, n2
                )
                conn.send(data.encode())
                key, _, n2_user = server_extract_message(
                    conn.recv(2048).decode(), public_key_user
                )

                if n2_user != n2:
                    print("n2 not same and valid")
                    break

                if not key:
                    is_close = True
                    break

                data = server_create_message(
                    "Enter Password Channel: ", SERVER, public_key_user, n2
                )
                conn.send(data.encode())
                input_password, _, n2_user = server_extract_message(
                    conn.recv(2048).decode(), public_key_user
                )
                if n2_user != n2:
                    print("n2 not same and valid")
                    break
                if not input_password:
                    is_close = True
                    break

                for i in database:
                    if i["key"] == key and i["password"] == hash(input_password):
                        conns = i["user"]
                        for j in i["user"]:
                            if j["username"] == username:
                                is_user_exist = True
                                break
                        else:
                            data = server_create_message(
                                "You are CONNECTED", SERVER, public_key_user, n2
                            )
                            conn.send(data.encode())
                            for k in conns:
                                sended_user_public_key = k["public_key"]
                                if sended_user_public_key is None:
                                    sended_user_public_key = lib.get_public_key(
                                        k["username"], PA_U
                                    )
                                k["conn"].send(
                                    server_create_message(
                                        f"{username} JOINED",
                                        SERVER,
                                        sended_user_public_key,
                                        k["n2"],
                                    ).encode()
                                )
                            i["user"].append(
                                {
                                    "username": username,
                                    "conn": conn,
                                    "public_key": None,
                                    "n2": n2,
                                }
                            )
                        break
                else:
                    data = server_create_message(
                        "Channel not found", SERVER, public_key_user, n2
                    )
                    conn.send(data.encode())
                    time.sleep(0.2)
                    continue

                break
            if is_close:
                print(f"Connection Close: {address}")
                conn.close()
                continue
        else:
            data = server_create_message("Menu not found", SERVER, public_key_user, n2)
            conn.send(data.encode())
            print(f"Connection Close: {address}")
            time.sleep(0.1)
            conn.close()
            continue

        if is_user_exist:
            data = server_create_message(
                "Username already exist ", SERVER, public_key_user, n2
            )
            print(f"Connection Close: {address}")
            conn.send(data.encode())
            conn.close()
        else:
            client_thread = threading.Thread(
                target=single_clinet, args=(conn, username, key)
            )
            client_thread.start()


if __name__ == "__main__":
    server_program()
