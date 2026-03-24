import os
from PIL import Image

# PNG validation/ Check
def validate_png(image_path):
    if not image_path.lower().endswith(".png"):
        raise ValueError("Only PNG images are supported to avoid compression.")

def encode_message(image_path, hex_message, output_path):
    validate_png(image_path)  # PNG check

    img = Image.open(image_path)
    
    if img.mode not in ['RGB', 'RGBA']:
        raise ValueError("Image must be in RGB or RGBA format")

    # Remove any spaces or '0x' prefix from hex input
    hex_message = hex_message.replace(' ', '').replace('0x', '')
    
    # Validate hex input
    try:
        # Convert hex to binary
        binary_message = bin(int(hex_message, 16))[2:]  # Remove '0b' prefix
        # Pad with leading zeros to ensure proper byte alignment
        binary_message = binary_message.zfill(len(hex_message) * 4)
    except ValueError:
        raise ValueError("Invalid hex input. Please enter valid hexadecimal characters (0-9, A-F)")

    # Add end marker (5 bytes = 40 bits)
    end_marker = '#####'
    end_binary = ''.join(format(ord(char), '08b') for char in end_marker)
    binary_message += end_binary

    required_pixels = len(binary_message) // 3
    if required_pixels > img.width * img.height:
        raise ValueError("Message is too long for the image")

    pixels = list(img.getdata())
    new_pixels = []

    for i in range(len(pixels)):
        pixel = list(pixels[i])
        
        if i * 3 < len(binary_message):
            # Embed bits into each color channel (R, G, B)
            for j in range(3):
                if i * 3 + j < len(binary_message):
                    # Get the LSB of the pixel channel
                    lsb = int(binary_message[i * 3 + j])
                    # Modify the pixel value to embed the bit
                    pixel[j] = (pixel[j] & ~1) | lsb
        
        new_pixels.append(tuple(pixel))

    # Create and save the new image and making sure no compression is applied
    new_img = Image.new(img.mode, img.size)
    new_img.putdata(new_pixels)
    new_img.save(output_path, format="PNG", optimize=False, compress_level=0)

    abs_path = os.path.abspath(output_path)
    print("Hex message successfully hidden in '{abs_path}' (No compression applied)")
    print("Stego image saved locally. You can now share it manually.")


def decode_message(image_path):
    validate_png(image_path)  # PNG check

    img = Image.open(image_path)
    
    if img.mode not in ['RGB', 'RGBA']:
        raise ValueError("Image must be in RGB or RGBA format")
    
    pixels = list(img.getdata())
    binary_message = ""
    
    # Extracting LSB from each pixel channel
    for pixel in pixels:
        for j in range(3):
            binary_message += str(pixel[j] & 1)
    
    # Convert binary to hex
    hex_message = ""
    for i in range(0, len(binary_message), 8):
        if i + 8 <= len(binary_message):
            byte = binary_message[i:i+8]
            char_code = int(byte, 2)
            hex_message += chr(char_code)
            
            # Check for end marker
            if hex_message.endswith('#####'):
                actual_message = hex_message[:-5]
                if actual_message:
                    hex_output = ''.join(format(ord(char), '02X') for char in actual_message)
                    return hex_output
                else:
                    return "00"  
    
    if actual_message:
        hex_output = ''.join(format(ord(char), '02X') for char in actual_message)
        return hex_output
    return "No message found or message incomplete"


# CLI for testing
if __name__ == "__main__":
    print("=== Image Steganography Tool (Hex Mode) ===")
    print("1. Encode a hex message in an image")
    print("2. Decode a hex message from an image")
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "1":
        # Encode message
        image_path = input("Enter the path to your input PNG image: ").strip()
        hex_message = input("Enter the hex message to hide (e.g., 48656C6C6F): ").strip()
        output_path = input("Enter the output image path (or press Enter for 'stego_image.png'): ").strip()
        
        if not output_path:
            output_path = "stego_image.png"
        
        try:
            encode_message(image_path, hex_message, output_path)
        except FileNotFoundError:
            print("Error: '{image_path}' not found. Please check the file path.")
        except Exception as e:
            print(f"An error occurred: {e}")
    
    elif choice == "2":
        # Decode message
        image_path = input("Enter the path to the stego PNG image: ").strip()
        
        try:
            decoded_hex = decode_message(image_path)
            print("Decoded hex message: " ,decoded_hex)
        except FileNotFoundError:
            print("Error: '{image_path}' not found. Please check the file path.")
        except Exception as e:
            print("An error occurred: {e}")
    
    else:
        print("Invalid choice. Please run the script again and select 1 or 2.")

