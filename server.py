# Recananya sih server bakal buka 2 koneksi gitu dan cuman bisa dua ?
# Atau kaya masukin key gitu, terus lawan bicara masukkan key nya ?
# Mereka sharking key jadi bisa banyak koneksi server bisa baca , kaya from
# client ini message tapi depracated

import json
import socket
import threading
import time
from os import pipe

import lib

database = []
# username

# message = {"sender": "", "body": ""}


def extract_message(message):
    message = json.loads(message)
    return message["body"], message["sender"]


def create_message(body, sender):
    return json.dumps({"sender": sender, "body": body})


def get_all_connection(key, username):
    for i in database:
        if i["key"] == key:
            return [user for user in i["user"] if user["username"] != username]
    return []


def single_clinet(conn, username, key):
    while True:
        print(f"Waiting message to {username}...")
        message, sender = extract_message(conn.recv(1024).decode())

        msg = create_message(message, sender)

        print(f"Message from {sender} : {message}")

        conns = get_all_connection(key, username)
        if username == sender:
            for j in conns:
                print(f"Sended to : {j['username']}")
                j["conn"].send(msg.encode())
        else:
            conn.send(msg.encode())

        if message.lower().strip() == "bye":
            # delete from database
            for chan in database:
                if chan["key"] == key:
                    chan["user"] = [
                        user for user in chan["user"] if user["username"] != username
                    ]
            break

    conn.close()


def server_program():
    host = socket.gethostname()
    port = 5056
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

        msg = create_message("\n1. Make New Channel\n2. Join Channel\n", "Server")
        conn.send(msg.encode())

        menu, username = extract_message(conn.recv(1024).decode())
        if not menu:
            break

        if menu == "1":
            key = lib.key_generation()
            data = create_message("Enter New Password: ", "Server")
            conn.send(data.encode())
            password, _ = extract_message(conn.recv(1024).decode())
            if not password:
                break

            database.append(
                {
                    "key": key,
                    "password": hash(password),
                    "user": [{"username": username, "conn": conn}],
                }
            )
            data = create_message(f"Channel Key : {key}", "Server")
            conn.send(data.encode())
            data = create_message(
                f"Channel Encryption Key : {lib.key_generation()}", "Server"
            )
            conn.send(data.encode())
        elif menu == "2":
            # Join Channeli
            while True:
                data = create_message("Enter Key Channel: ", "Server")
                conn.send(data.encode())
                key, _ = extract_message(conn.recv(1024).decode())
                if not key:
                    break

                data = create_message("Enter Password Channel: ", "Server")
                conn.send(data.encode())
                input_password, _ = extract_message(conn.recv(1024).decode())
                if not input_password:
                    break

                for i in database:
                    if i["key"] == key and i["password"] == hash(input_password):
                        conns = i["user"]
                        for j in i["user"]:
                            if j["username"] == username:
                                is_user_exist = True
                                break
                        else:
                            data = create_message(
                                "You are connected start chating", "Server"
                            )
                            conn.send(data.encode())
                            for k in conns:
                                k["conn"].send(
                                    create_message(
                                        f"{username} has joined the channel", "Server"
                                    ).encode()
                                )
                            i["user"].append({"username": username, "conn": conn})
                        break
                else:
                    data = create_message("Channel not found", "Server")
                    conn.send(data.encode())
                    time.sleep(0.2)
                    continue

                break

        if is_user_exist:
            data = create_message(
                "Username already exist, Enter 2 times to close ", "Server"
            )
            conn.send(data.encode())
            conn.close()
        else:
            client_thread = threading.Thread(
                target=single_clinet, args=(conn, username, key)
            )
            client_thread.start()


if __name__ == "__main__":
    server_program()
