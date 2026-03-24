from key_manager import generate_and_display_keys

if __name__ == "__main__":
    print("🔑 Generating RSA key pair...")
    generate_and_display_keys()
    print("\n⚠️ Keep the PRIVATE KEY secret!")
    print("   Share the PUBLIC KEY with others")