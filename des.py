# DES algorithm from stratch
# Without using any library
import lib

# plain = input("Enter Plain text:")
# key = lib.key_generation()
# chiper = lib.des_encrypt(plain, key)
# print(chiper)
# print(lib.des_decrypt(chiper, key))
# Menu
while True:
    print("1. Generate Key")
    print("2. Encrypt")
    print("3. Decrypt")
    print("4. Exit")

    menu = input("Select Menu: ")
    if menu == "1":
        print("Key: ", lib.key_generation())
    elif menu == "2":
        plain = input("Enter Plain Text: ")
        key = input("Enter Key: ")
        # check if key is 64 bit
        if len(key) * 4 != 64:
            print("Key must be 64 bit")
            continue
        print("Chiper Text: ", lib.des_encrypt(plain, key))
    elif menu == "3":
        ciper = input("Enter Ciper Text: ")
        key = input("Enter 64 Key: ")
        # check if key is 64 bit
        if len(key) * 4 != 64:
            print("Key must 64 bit")
            continue
        print("Plain Text: ", lib.des_decrypt(ciper, key))
    elif menu == "4":
        break
    else:
        print("Invalid Menu")
        continue
