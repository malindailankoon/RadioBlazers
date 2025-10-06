def CRC_adder(bits):
    poly = 0x104C11DB7

    data = int(bits, 2)
    data <<= 32  # make room for CRC32

    poly_length = poly.bit_length()

    while data.bit_length() >= poly_length:
        data ^= poly << (data.bit_length() - poly_length)

    crc_bits = format(data, "032b")  # CRC32 result
    newbits = bits + crc_bits        # original bits + CRC

    return newbits

def write_bits_to_file(bitstream, filename="output.tmp"):
    # pad to nearest byte
    if len(bitstream) % 8 != 0:
        bitstream += "0" * (8 - len(bitstream) % 8)

    byte_data = bytes(int(bitstream[i:i+8], 2) for i in range(0, len(bitstream), 8))
    with open(filename, "wb") as f:
        f.write(byte_data)

# Example
bits = "11101010"
newbits = CRC_adder(bits)
write_bits_to_file(newbits)

print("Written to output.tmp")

