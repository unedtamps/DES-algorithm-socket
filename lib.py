import os
import socket
import time

import tables
from rsa import RSA


def hex_to_binary(hex_string):
    decimal_value = int(hex_string, 16)
    return bin(decimal_value)[2:].zfill(64)


def binary_to_hex(binary_string):
    return hex(int(binary_string, 2))[2:].zfill(16)


def string_to_binary(input_string):
    binary_rep = "".join(format(ord(i), "08b") for i in input_string)
    # split to array of 64 bits
    binary_reps_64 = [binary_rep[i : i + 64] for i in range(0, len(binary_rep), 64)]
    # padding the last elemnt if not 64 bits
    binary_reps_64[-1] = binary_reps_64[-1].zfill(64)
    return binary_reps_64


def binary_to_ascii(binary_str):
    return "".join(
        [chr(int(binary_str[i : i + 8], 2)) for i in range(0, len(binary_str), 8)]
    )


def initial_permutate(binary_64):
    return "".join([binary_64[i - 1] for i in tables.IP])


def key_generation():
    return os.urandom(8).hex()


def key_rounded(binary_key):
    # 56 bits key
    pc_1_key = "".join([binary_key[i - 1] for i in tables.PC_1])

    # split to 28 bits
    l = pc_1_key[:28]
    r = pc_1_key[28:]
    rounded_key = []
    # perform 16 rounds
    for i in range(16):
        l = l[tables.SHIFT[i] :] + l[: tables.SHIFT[i]]
        r = r[tables.SHIFT[i] :] + r[: tables.SHIFT[i]]
        lr = l + r

        # PC 2
        rounded_key.append("".join([lr[i - 1] for i in tables.PC_2]))

    return rounded_key


def des_encrypt(plain_text, key):
    # 64 bits binary plain text
    # hex_plain_text = plain_text.encode("utf-8").hex()
    # binary_64_arr = [
    #     hex_to_binary(hex_plain_text[i : i + 16])
    #     for i in range(0, len(hex_plain_text), 16)
    # ]
    binary_64_arr = string_to_binary(plain_text)
    round_keys = key_rounded(hex_to_binary(key))
    cipers = []

    for bin_64 in binary_64_arr:
        # initial_permutation
        ip_str = initial_permutate(bin_64)

        # split to 32 bits
        left_pt = ip_str[:32]
        right_pt = ip_str[32:]

        for i in range(16):
            # expansion
            expand_right_pt = "".join([right_pt[i - 1] for i in tables.EXPANSION])
            round_key = round_keys[i]

            # xor with round key
            xor_result = bin(int(expand_right_pt, 2) ^ int(round_key, 2))[2:].zfill(48)

            # split into 8 blocks of 6 bits
            xor_blocks = [xor_result[i : i + 6] for i in range(0, len(xor_result), 6)]
            s_box_result = ""

            for j in range(8):
                row = int(xor_blocks[j][0] + xor_blocks[j][-1], 2)
                col = int(xor_blocks[j][1:-1], 2)
                s_box_result += format(tables.S_BOXS[j][row][col], "04b")

            # Permutation using P_BOX
            p_box_res = "".join([s_box_result[i - 1] for i in tables.P_BOX])

            # xor with left plain text

            new_right_pt = bin(int(p_box_res, 2) ^ int(left_pt, 2))[2:].zfill(32)

            left_pt = right_pt
            right_pt = new_right_pt

        # final permutation
        final_pt = right_pt + left_pt
        final_cp = "".join([final_pt[i - 1] for i in tables.IP_REVERSE])
        cipers.append(binary_to_hex(final_cp))

    return "".join(cipers)


def des_decrypt(ciper_text, key):
    round_keys = key_rounded(hex_to_binary(key))

    # devide chiper_tex to 64 bit each
    chiper_text_64 = [ciper_text[i : i + 16] for i in range(0, len(ciper_text), 16)]
    plaintext = []
    for cp_text in chiper_text_64:
        bin_cp = hex_to_binary(cp_text)
        ip_str = initial_permutate(bin_cp)

        left_pt = ip_str[:32]
        right_pt = ip_str[32:]

        for i in range(16):
            expand_right_pt = "".join([right_pt[i - 1] for i in tables.EXPANSION])
            round_key = round_keys[15 - i]

            xor_result = bin(int(expand_right_pt, 2) ^ int(round_key, 2))[2:].zfill(48)

            # split into 8 blocks of 6 bits
            xor_blocks = [xor_result[i : i + 6] for i in range(0, len(xor_result), 6)]
            s_box_result = ""

            for j in range(8):
                row = int(xor_blocks[j][0] + xor_blocks[j][-1], 2)
                col = int(xor_blocks[j][1:-1], 2)
                s_box_result += format(tables.S_BOXS[j][row][col], "04b")

            # Permutation using P_BOX
            p_box_res = "".join([s_box_result[i - 1] for i in tables.P_BOX])

            # xor with left plain text

            new_right_pt = bin(int(p_box_res, 2) ^ int(left_pt, 2))[2:].zfill(32)

            left_pt = right_pt
            right_pt = new_right_pt
        final_pt = right_pt + left_pt
        final_pl = "".join([final_pt[i - 1] for i in tables.IP_REVERSE])
        # print(f"{ks} = {final_pl}")

        plaintext.append(binary_to_ascii(final_pl))

    return "".join(plaintext)


def send_public_key(send_key, username, encrypt_key):
    pka_host = socket.gethostname()
    pka_port = int(os.getenv("PKA_PORT", "5000"))
    pka_server_socket = socket.socket()
    pka_server_socket.connect((pka_host, pka_port))
    pka_server_socket.send("1".encode())
    time.sleep(0.1)
    e, n = send_key
    msg = f"{username},{e},{n}"
    encrypt_message = RSA().encrypt(encrypt_key, msg)
    pka_server_socket.send(list_to_string(encrypt_message).encode())


def get_public_key(username, encrypt_key):
    pka_host = socket.gethostname()
    pka_port = int(os.getenv("PKA_PORT", "5000"))
    pka_server_socket = socket.socket()
    pka_server_socket.connect((pka_host, pka_port))
    pka_server_socket.send("2".encode())
    time.sleep(0.1)
    username = RSA().encrypt(encrypt_key, username)

    pka_server_socket.send(list_to_string(username).encode())
    msg = pka_server_socket.recv(1024).decode()
    msg = string_to_list(msg)
    msg = RSA().decrypt(encrypt_key, msg)
    msg = msg.split(",")
    return int(msg[0]), int(msg[1])


def list_to_string(int_list):
    result = ",".join(str(num) for num in int_list)
    return result


def string_to_list(string):
    return list(map(int, string.split(",")))
