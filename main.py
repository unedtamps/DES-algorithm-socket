# DES algorithm from stratch
# Without using any library
import lib

key = lib.key_generation()
plain_text = input("Enter Plain Text: ")

print("Key ", key)

ciper_text = lib.des_encrypt(plain_text, key)
print("Ciper Text", ciper_text)


print("Plain text:", lib.des_decrypt(ciper_text, key))
