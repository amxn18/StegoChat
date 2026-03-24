from chacha import chacha_encrypt, chacha_decrypt
from crypto_utils import generate_salt



# (1) ACTUAL ENCRYPTION TEST
message = input("Enter the message to encrypt: ")  # Get user input for the message
password = input("Enter the password: ")  # Get user input for the password

# Encrypt
encrypted = chacha_encrypt(message, password)  # Call the function
print(f"\nCipher text: {encrypted.hex()}")  # Print the output
