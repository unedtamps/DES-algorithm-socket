import json
import os
import socket
import threading
import time

import lib

database = []
# username
SERVER_KEY = "db4b60092e536e47"
SERVER = "SERVER"


def extract_message(message):
    if not message:
        return "", ""
    message = json.loads(message)
    return message["body"], message["sender"]


def create_message(body, sender):
    return json.dumps({"sender": sender, "body": body})


def server_create_message(body, sender):
    return json.dumps({"sender": sender, "body": lib.des_encrypt(body, SERVER_KEY)})


def server_extract_message(message):
    if not message:
        return "", ""
    message = json.loads(message)
    return lib.des_decrypt(message["body"], SERVER_KEY), message["sender"]


def get_all_connection(key, username):
    for i in database:
        if i["key"] == key:
            return [user for user in i["user"] if user["username"] != username]
    return []


def single_clinet(conn, username, key):
    while True:
        # print(f"Waiting message to {username}...")
        message, sender = extract_message(conn.recv(1024).decode())

        if not message:
            break

        msg = create_message(message, sender)

        print(f"Message from {sender} : {message}")

        conns = get_all_connection(key, username)
        if username == sender:
            for j in conns:
                print(f"Sended to : {j['username']}")
                j["conn"].send(msg.encode())
        else:
            conn.send(msg.encode())

    print(f"Connection Close: {username}")
    for chan in database:
        if chan["key"] == key:
            chan["user"] = [
                user for user in chan["user"] if user["username"] != username
            ]

    for j in get_all_connection(key, username):
        print(f"Sended to : {j['username']}")
        data = server_create_message(f"{username} DISCONNECTED", SERVER)
        j["conn"].send(data.encode())
    conn.close()


def server_program():
    host = socket.gethostname()
    port = int(os.environ["PORT"])
    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen()

    while True:
        print("Waiting for connections ...")
        conn, address = server_socket.accept()  # accept new connection
        print("Connection from: " + str(address))
        username = ""
        key = ""
        is_user_exist = False

        # Send menu to the client

        msg = server_create_message(
            "\n1. Make New Channel\n2. Join Channel\n",
            SERVER,
        )
        conn.send(msg.encode())

        menu, username = server_extract_message(conn.recv(1024).decode())
        if not menu:
            print(f"Connection Close: {address}")
            conn.close()
            continue
        menu = menu.replace("\x00", "")

        if username.lower().strip() == SERVER.lower().strip():
            data = server_create_message("Username not avaliable: ", SERVER)
            conn.send(data.encode())
            print(f"Connection Close: {address}")
            time.sleep(0.1)
            conn.close()
            continue

        if menu == "1":
            key = lib.key_generation()
            data = server_create_message("Enter New Password: ", SERVER)
            conn.send(data.encode())
            password, _ = server_extract_message(conn.recv(1024).decode())
            if not password:
                print(f"Connection Close: {address}")
                conn.close()
                continue

            database.append(
                {
                    "key": key,
                    "password": hash(password),
                    "user": [{"username": username, "conn": conn}],
                }
            )
            data = server_create_message(f"Channel Key : {key}", SERVER)
            conn.send(data.encode())
            time.sleep(0.1)
            data = server_create_message("Your are CONNECTED", SERVER)
            conn.send(data.encode())
            time.sleep(0.1)
        elif menu == "2":
            # Join Channeli
            is_close = False
            while True:
                data = server_create_message("Enter Key Channel: ", SERVER)
                conn.send(data.encode())
                key, _ = server_extract_message(conn.recv(1024).decode())
                if not key:
                    is_close = True
                    break

                data = server_create_message("Enter Password Channel: ", SERVER)
                conn.send(data.encode())
                input_password, _ = server_extract_message(conn.recv(1024).decode())
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
                            data = server_create_message("You are CONNECTED", SERVER)
                            conn.send(data.encode())
                            for k in conns:
                                k["conn"].send(
                                    server_create_message(
                                        f"{username} JOINED", SERVER
                                    ).encode()
                                )
                            i["user"].append({"username": username, "conn": conn})
                        break
                else:
                    data = server_create_message("Channel not found", SERVER)
                    conn.send(data.encode())
                    time.sleep(0.2)
                    continue

                break
            if is_close:
                print(f"Connection Close: {address}")
                conn.close()
                continue
        else:
            data = server_create_message("Menu not found", SERVER)
            conn.send(data.encode())
            print(f"Connection Close: {address}")
            time.sleep(0.1)
            conn.close()
            continue

        if is_user_exist:
            data = server_create_message("Username already exist ", SERVER)
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
