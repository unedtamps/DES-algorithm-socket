import json
import socket
import threading


def extract_message(message):
    message = json.loads(message)
    return message["body"], message["sender"]


def create_message(body, sender):
    return json.dumps({"sender": sender, "body": body})


# def recive_message(client_socket):
#     message, sender = extract_message(client_socket.recv(1024).decode())
#     print(f"({sender}) {message}")


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5051  # socket server port number

    username = input("Input your username: ")

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server

    # client_thread = threading.Thread(target=recive_message, args=(client_socket,))
    # client_thread.start()

    while True:
        message, sender = extract_message(client_socket.recv(1024).decode())
        print(f"({sender}) {message}")
        message = input(" -> ")  # take input

        client_socket.send(create_message(message, username).encode())  # send message

        if message.lower().strip == "bye":
            break

    client_socket.close()  # close the connection


if __name__ == "__main__":
    client_program()
