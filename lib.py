import os

import tables


def hex_to_binary(hex_string):
    decimal_value = int(hex_string, 16)
    return bin(decimal_value)[2:].zfill(64)


def string_to_binary(input_string):
    binary_rep = "".join(format(ord(i), "08b") for i in input_string)
    # split to array of 64 bits
    binary_reps_64 = [binary_rep[i : i + 64] for i in range(0, len(binary_rep), 64)]

    # padding the last elemnt if not 64 bits
    binary_reps_64[-1] = binary_reps_64[-1].ljust(64, "0")

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
        cipers.append(hex(int(final_cp, 2))[2:])
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
        plaintext.append(binary_to_ascii(final_pl))

    return "".join(plaintext)
