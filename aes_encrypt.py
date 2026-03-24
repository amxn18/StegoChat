from aes import aes_encrypt

# Encrypt
secret_message = input("Enter the message to encrypt: ")
password = input("Enter the password: ")
encrypted = aes_encrypt(secret_message, password)
print(f"Encrypted: {encrypted.hex()}")
