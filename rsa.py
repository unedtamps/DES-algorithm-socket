import random

from sympy import isprime


class RSA:
    def __gcd(self, a, b):
        while b != 0:
            a, b = b, a % b
        return a

    def __mod_inverse(self, e, phi):
        d = 0
        x1, x2, x3 = 1, 0, phi
        y1, y2, y3 = 0, 1, e
        while y3 != 1:
            q = x3 // y3
            t1, t2, t3 = x1 - q * y1, x2 - q * y2, x3 - q * y3
            x1, x2, x3 = y1, y2, y3
            y1, y2, y3 = t1, t2, t3
            d = y2 % phi
        return d

    def __generate_prime(self, start, end):
        while True:
            p = random.randint(start, end)
            if isprime(p):
                return p

    def generate_keys(self):
        # Generate two random prime numbers
        p = self.__generate_prime(1000, 2000)
        q = self.__generate_prime(1000, 2000)
        while p == q:  # Ensure p and q are distinct
            q = self.__generate_prime(1000, 3000)

        n = p * q
        phi = (p - 1) * (q - 1)

        # Choose e such that 1 < e < phi and gcd(e, phi) = 1
        e = random.randint(2, phi - 1)
        while self.__gcd(e, phi) != 1:
            e = random.randint(2, phi - 1)

        # Calculate d
        d = self.__mod_inverse(e, phi)

        # Public and private keys
        return (e, n), (d, n)

    # RSA Encryption
    def encrypt(self, public_key, plaintext):
        e, n = public_key
        ciphertext = [pow(ord(char), e, n) for char in plaintext]
        return ciphertext

    # RSA Decryption
    def decrypt(self, private_key, ciphertext):
        d, n = private_key
        plaintext = "".join([chr(pow(char, d, n)) for char in ciphertext])
        return plaintext


# if __name__ == "__main__":
#     public_key, private_key = RSA().generate_keys()
#     print(public_key)
#     print(private_key)
